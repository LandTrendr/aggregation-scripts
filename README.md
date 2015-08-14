This is a set of scripts to summarize biomass and change agent data.

**stackagents.py**
This script loops through a prioritized list of change agent maps (located in parameters folder) and combines these sources into a yearly raster stack. The key for outputs is also located in the parameters folder.

>Usage: python stackagents.py [modelregion] [outputfile]

>Example: python stackagents.py mr224 /projectnb/trenders/proj/aggregation/outputs/mr224/change_agent_maps/mr224_agent_aggregation.bsq


**deltaBiomass.py**
This script creates raster stacks of yearly change in biomass values. Biomass data sources are specified in a parameter text file.

>Usage: python deltaBiomass.py [path/to/parameterfile]

Example Parameter File:
'''
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
'''
