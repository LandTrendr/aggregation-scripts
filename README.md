This is a set of scripts to summarize biomass and change agent data.

**stackagents.py**
This script loops through a prioritized list of change agent maps (located in parameters folder) and combines these sources into a yearly raster stack. The key for outputs is also located in the parameters folder.

>Usage: python stackagents.py [modelregion] [outputfile]

>Example: python stackagents.py mr224 /projectnb/trenders/proj/aggregation/outputs/mr224/change_agent_maps/mr224_agent_aggregation.bsq*



