This is a set of scripts to summarize biomass and change agent data.
____________________________________________________________________

**stackagents.py**
This script loops through a prioritized list of change agent maps (located in parameters folder) and combines these sources into a yearly raster stack. 

>Usage: python stackagents.py [modelregion] [outputfile]

>Example: python stackagents.py mr224 /projectnb/trenders/proj/aggregation/outputs/mr224/change_agent_maps/mr224_agent_aggregation.bsq

Change Agent Output Key:
```
0: No Agent
1: Clearcut
2: Partial Harvest
3: Development
4: Fire
6: Insect/Disease
7: Road
9: False Change
10: Unknown Agent
11: Water
15: Debris Flow
17: Other
18: No Name
21: MPB-29
22: MPB-239
25: WSB-29
26: WSB-239
30: Longest Disturbance
40: Greatest Disturbance
51: Growth
```




**deltaBiomass.py**
This script creates raster stacks of yearly change in biomass values. Biomass data sources are specified in a parameter text file.

>Usage: python deltaBiomass.py [path/to/parameterfile]

Example Parameter File:
```
MR224 Post Tassel Cap Biomass Params
region: mr224
name: delta_tc_nbr_k1_bph_ge_3
name: delta_tc_nbr_k1_bph_ge_3_crm
name: delta_tc_nbr_k1_bph_ge_3_jenk
name: delta_tc_nbr_k5_bph_ge_3
biomass:/projectnb/trenders/proj/cmonster/mr224/biomassApril2014/nbr/tc_nbr_k1/bph_ge_3
biomass:/projectnb/trenders/proj/cmonster/mr224/biomassApril2014/nbr/tc_nbr_k1/bph_ge_3_crm
biomass:/projectnb/trenders/proj/cmonster/mr224/biomassApril2014/nbr/tc_nbr_k1/bph_ge_3_jenk
biomass:/projectnb/trenders/proj/cmonster/mr224/biomassApril2014/nbr/tc_nbr_k5/bph_ge_3
```
**summarizeBiomassByAgent.py**
This script creates CSV files containing yearly total change in biomass values for each change agent.

>Usage: python summarizeBiomassByAgent.py [modelregion] [crm/jenk]

>Example: python summarizeBiomassByAgent.py mr224 jenk
