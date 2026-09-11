"""Structural-first Connectivity v2.  Role evidence explains links; it never creates the baseline."""
from __future__ import annotations
import copy
from collections import Counter
from typing import Any
import positional_relationships
import role_behaviours
import role_constraints

_LANE = {"left": 0, "centre": 1, "right": 2}

def _semantics(kb, catalog):
    refs={(r["role_behaviour_ref"] or {}).get("phase", "")+":"+(r["role_behaviour_ref"] or {}).get("role", ""):r["internal_id"] for r in catalog}
    out={}
    for entry in kb:
        if not entry.get("behaviour_verified"): continue
        rid=entry.get("role_internal_id") or refs.get(entry["phase"]+":"+entry["role"])
        if not rid: continue
        for behaviour in entry["behaviours"]:
            if behaviour.get("verification") not in {"official","verified","user_ingame_verified"}: continue
            for group, items in behaviour.get("connectivity_semantics", {}).items():
                for item in items:
                    out.setdefault(rid,[]).append({"group":group,"semantic_id":item["semantic_id"],"behaviour_id":behaviour["behaviour_id"],"evidence_ids":copy.deepcopy(item["evidence_ids"])})
    return out

def _nodes(tactic, catalog, kb, aliases):
    resolved=role_constraints.resolve_catalog(catalog,kb)
    by_abbr={}
    for role in resolved:
        if role["phase"] == "IP" and role.get("display_abbr"): by_abbr.setdefault(role["display_abbr"],[]).append(role)
    semantics=_semantics(kb,catalog); nodes=[]
    for position, token in (tactic.get("ip_roles") or {}).items():
        canonical=aliases.get(("IP",token),token) if isinstance(token,str) else token
        matches=by_abbr.get(canonical,[]) if isinstance(canonical,str) else []
        role=matches[0] if len(matches)==1 else None
        node=positional_relationships.build_position_node("IP",position,role["internal_id"] if role else None)
        node.update({"resolved_role":{"status":"resolved","role_name_ko":role["role_name_ko"]} if role else {"status":"unresolved","raw_value":token},"role_modifiers":semantics.get(role["internal_id"],[]) if role else []})
        nodes.append(node)
    return nodes

def _link(source,target, adjacent_occupied_bands):
    if not isinstance(source["vertical_index"],int) or not isinstance(target["vertical_index"],int): return None
    sv,tv=source["vertical_index"],target["vertical_index"]; delta=tv-sv
    sl,tl=source["lateral_slot"],target["lateral_slot"]
    lateral_delta=abs(_LANE[sl]-_LANE[tl]) if sl in _LANE and tl in _LANE else None
    if lateral_delta is None or lateral_delta>1: return None
    occupied_forward = delta > 0 and (sv, tv) in adjacent_occupied_bands
    if abs(delta)>2 and not occupied_forward: return None
    if delta==0: relation="same_line_support"; direction="support"; progression="support"
    elif delta>0: relation="forward_progression" if lateral_delta==0 else "diagonal_progression"; direction="forward"; progression="forward"
    else: relation="recycle"; direction="backward"; progression="recycle"
    relation_facts=positional_relationships.calculate_configured_position_relation(source,target)["configured_position_relation"]
    modifiers=[]
    for item in source["role_modifiers"]:
        if item["group"]=="send": modifiers.append({**item,"applies_to":"source"})
    for item in target["role_modifiers"]:
        if item["group"]=="receive": modifiers.append({**item,"applies_to":"target"})
    return {"link_id":f"{source['node_id']}->{target['node_id']}","source":source["node_id"],"target":target["node_id"],"relation_type":relation,"direction":direction,"progression_value":progression,"lateral_relation":"same_lane" if lateral_delta==0 else "adjacent_lane","vertical_relation":relation_facts["relations"],"structural_basis":{"adjacency_basis":"occupied_line_adjacency" if occupied_forward and abs(delta)>2 else "absolute_band_adjacency","source_band":source["vertical_band"],"target_band":target["vertical_band"],"source_lane":sl,"target_lane":tl,"absolute_band_delta":delta},"role_modifiers":modifiers,"limitations":["Structural link is a candidate route, not an observed pass or success estimate."]}

def _routes(nodes,links):
    forward={n["node_id"]:[] for n in nodes}
    for link in links:
        if link["direction"]=="forward": forward[link["source"]].append(link["target"])
    starts=[n for n in nodes if n["vertical_index"] in (0,1)]
    ends={n["node_id"] for n in nodes if n["vertical_band"]=="forward"}; found=[]
    def walk(path):
        cur=path[-1]
        if cur in ends and len(path)>1: found.append(path); return
        if len(path)>=6: return
        for nxt in forward.get(cur,[]):
            if nxt not in path: walk(path+[nxt])
    for node in starts: walk([node["node_id"]])
    unique=[]; seen=set()
    for path in found:
        key=tuple(path)
        if key not in seen: seen.add(key); unique.append({"route_id":"->".join(path),"node_ids":path,"status":"structural_route","limitations":["Route is positional structure only; role behaviour may be unverified."]})
    return unique

def _display_plan(nodes, links, routes):
    """UI-only link classification; never used by topology or route traversal."""
    by_id={node["node_id"]: node for node in nodes}
    families={"left": [], "centre": [], "right": []}
    for route in routes:
        slots=[by_id[node_id]["lateral_slot"] for node_id in route["node_ids"][1:] if by_id[node_id]["lateral_slot"] in _LANE]
        region=next((slot for slot in slots if slot in {"left", "right"}), "centre")
        families[region].append(route)
    representatives=[]; primary_ids=set()
    for region, candidates in families.items():
        if not candidates: continue
        representative=min(candidates, key=lambda route: (len(route["node_ids"]), route["route_id"]))
        representatives.append({"region":region,"representative_route_id":representative["route_id"],"node_ids":representative["node_ids"],"alternative_route_ids":[route["route_id"] for route in candidates if route["route_id"]!=representative["route_id"]]})
        primary_ids.update(f"{source}->{target}" for source,target in zip(representative["node_ids"], representative["node_ids"][1:]))
    classified=[]
    for link in links:
        if link["link_id"] in primary_ids:
            presentation_class="PRIMARY"; default_visible=True
        elif link["direction"]=="forward" and link["role_modifiers"]:
            presentation_class="SECONDARY"; default_visible=True
        elif link["direction"]=="forward":
            presentation_class="SECONDARY"; default_visible=False
        else:
            presentation_class="HIDDEN_DEFAULT"; default_visible=False
        classified.append({**link,"presentation_class":presentation_class,"default_visible":default_visible})
    counts={kind:sum(link["presentation_class"]==kind for link in classified) for kind in ("PRIMARY","SECONDARY","HIDDEN_DEFAULT")}
    return classified,{"route_families":representatives,"counts":counts,"default_visible_count":sum(link["default_visible"] for link in classified),"full_link_count":len(classified),"limitations":["Display priority is UI-only and does not alter structural topology or route detection."]}

def build_connectivity_v2(tactic: dict[str,Any], catalog=None, behaviour_kb=None, aliases=None):
    catalog=role_constraints.load_role_catalog() if catalog is None else role_constraints.validate_role_catalog(catalog)
    kb=role_behaviours.load_knowledge_base() if behaviour_kb is None else role_behaviours.validate_knowledge_base(behaviour_kb)
    aliases={} if aliases is None else aliases
    nodes=_nodes(tactic,catalog,kb,aliases)
    occupied=sorted({node["vertical_index"] for node in nodes if isinstance(node["vertical_index"], int)})
    adjacent_occupied_bands=set(zip(occupied, occupied[1:]))
    links=[link for s in nodes for t in nodes if s["node_id"]!=t["node_id"] if (link:=_link(s,t,adjacent_occupied_bands))]
    routes=_routes(nodes,links); links,display_plan=_display_plan(nodes,links,routes); counts=Counter(n for route in routes for n in route["node_ids"][1:-1]); bottlenecks=[{"node_id":n,"status":"shared_progression_connector","route_ids":[r["route_id"] for r in routes if n in r["node_ids"]],"limitation":"A shared connector is neutral structure, not a tactical-quality judgement."} for n,c in counts.items() if c>1]
    regions={lane:{"nodes":[n["node_id"] for n in nodes if n["lateral_slot"]==lane],"structural_links":[l["link_id"] for l in links if next(n for n in nodes if n["node_id"]==l["source"])["lateral_slot"]==lane or next(n for n in nodes if n["node_id"]==l["target"])["lateral_slot"]==lane],"forward_routes":[r["route_id"] for r in routes if any(next(n for n in nodes if n["node_id"]==x)["lateral_slot"]==lane for x in r["node_ids"])]} for lane in ("left","centre","right")}
    return {"nodes":nodes,"structural_links":links,"progression_routes":routes,"bottlenecks":bottlenecks,"network_regions":regions,"display_plan":display_plan,"role_modifiers":[{"node_id":n["node_id"],"items":n["role_modifiers"]} for n in nodes if n["role_modifiers"]],"observations":[{"type":"structural_links_present","count":len(links)},{"type":"forward_progression_routes_present","count":len(routes)}],"limitations":["Configured positions create baseline links; role evidence only explains modifiers.","No score, pass probability, match outcome or actual player location is inferred.","Team instructions do not affect Connectivity v2 in this phase."]}
