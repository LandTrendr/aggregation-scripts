##CMonster Graphing - Area by Agent Chart

# install.packages("ggplot2")
library(ggplot2)
#install.packages("plyr")
library(plyr)
#install.packages("ggthemes")
library(ggthemes)

#set working directory for new data
setwd("/vol/v1/proj/aggregation/outputs/mr224/summary_tables/")
data=read.csv("mr224_agent_hectares_summary_agent_key_reduced.csv", header = T)

#define exclusion function
`%notin%` <- function(x,y) !(x %in% y) 



##Rearrange data to rows instead of columns###
new=NULL
###start loop from column 3 until the end
for(i in 3:ncol(data)){
  ####row bind to new/null with the metadata from columns 1:2, attach thier names, the append looped yearly area data
  ##the data[1:2] references the columns with metadata; the (data)[i],2,5 references the year data from within the coloumn names 
  new=rbind(new, cbind(data[1:2], as.numeric(substr(colnames(data)[i],2,5)), data[,i]))
	}
	
##'new' sans the NA's; [,4] is the column reference for the new column we just created
new=new[!is.na(new[,4]),]

#rename the dataframe
df=new
#rename the columns
colnames(df)[2]<-"Agent"
colnames(df)[3]<-"Year"
colnames(df)[4]<-"Area"

#Create a separate dataset summing the yearly change in area from all agents
test=by(df$Area, df$Year, sum)
list=as.data.frame(cbind(c(test)))
Year=row.names(list)
list$Year<-Year
colnames(list)[1]="Year.Sum"

#join the yearly total change in area back into the original dataset
bigdf=join(df, list, type="left")


#Change the draw order for coloring and stacking
#Order the Agents the way you want them to be stacked for graphing
# these names need to match with what's in your CSV file, or else you'll get an NA

#REDUCED ALL#
#order = c("Fire", "Clearcut", "Partial Harvest", "Development", "Insects/Disease",
#          "Long Slow Disturbance", "Fast Disturbance", "No Agent", "Growth")

#REDUCED DISTURBANCES ONLY#
order = c("Fire", "Clearcut", "Partial Harvest", "Development", "Insects/Disease",
          "Long Slow Disturbance", "Fast Disturbance")

bigdf = subset(bigdf, Agent %in% order)
bigdf$Agent<-factor(bigdf$Agent, levels=order)

###COLOR SETUP FOR ALL GRAPHS
#Make up a rainbow palette

##ALL REDUCED CATS##
pal=palette(rainbow(7))

pal[2]="#543005" #clearcut-brown
pal[4]="#cab2d6" #development-light purple
pal[7]= "#710162" #fast disturbance-purple
pal[1]= "#d33502" #fire-red
#pal[9]= "#017354" #growth-green
pal[5]= "#ef6a32" #insects/disease-orange
pal[6]= "#fbbf45" #long slow disturbance-yellow
#pal[8]= "#bbb9b2" #no agent-grey
pal[3]="#3b87bd" #partial harvest-light blue


yrange = c(0,1.25)
xrange = c(1990,2010)
ranges=data.frame(xrange,yrange)
colnames(ranges)[1] = "X"
colnames(ranges)[2] = "Y"

#####ACTUAL PLOTTING CODE!!!#########
plot.new()
setwd("/vol/v1/proj/aggregation/figs/")
p<-ggplot()+
  geom_bar(aes(Year, Area/1e6, fill=Agent, order=Agent), bigdf, stat="identity", position="stack")+
  ylab("Total Area (Million Hectares)")+
  xlab("Year")+
  #geom_abline(intercept=0, slope=0, colour="black", size=1)+
  scale_fill_manual(values=pal, guide=guide_legend(reverse=TRUE))+
  scale_y_continuous(limits=yrange)+
  geom_rangeframe(data=ranges, mapping=aes(x=X, y=Y))+
  theme_tufte(base_size=20, base_family="BemboStd")+
  theme(axis.title.x=element_text(size=rel(2)))+
  theme(axis.title.y=element_text(size=rel(2)))+
  theme(axis.text.x=element_text(size=rel(1.5), vjust=0.45))+
  theme(axis.text.y=element_text(size=rel(1.5), vjust=0.45))+
  theme(legend.title=element_text(size=rel(1.25)))+
  theme(legend.text=element_text(size=rel(1)))+
  scale_x_continuous(limits= xrange, breaks=seq(1990,2010,5))
p<-p+theme(axis.title.x=element_text(size=rel(1.75)))
p<-p+theme(axis.title.y=element_text(size=rel(1.75)))
p<-p+theme(axis.text.x=element_text(angle=90, size=rel(1.5), vjust=0.45))
p
#pdf("mr224_area_barchart_exclgrowth.pdf")
plot(p)
#dev.off()
