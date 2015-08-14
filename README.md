*This is a set of scripts to summarize biomass and change agent data.*

**stackagents.py**
This script loops through a prioritized list of change agent maps (located in parameters folder) and combines these sources into a yearly raster stack. 

>Usage: python stackagents.py [modelregion] [outputfile]

>Example: python stackagents.py mr224 /projectnb/trenders/proj/aggregation/outputs/mr224/change_agent_maps/mr224_agent_aggregation.bsq

Change Agent Output Key:
```
1: Clearcut
2: Partial Harvest
3: Development
4: Fire
5: Salvage
6: Insect/Disease
7: Road
8: No Visible Change
9: False Change
10: Unknown Agent
11: Water
12: Wind
13: Avalanche: chute
14: Avalanche: runout
15: Debris flow
16: Landslide
17: Other

21: MPB - 29
22: MPB - 239

25: WSB - 29
50: mr224 wetness longest recovery2, unfiltered

26: WSB - 239

30: mr224 longest disturbance, unfiltered
40: mr224 greatest fast disturbance, unfiltered
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
