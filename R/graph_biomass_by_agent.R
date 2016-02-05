##CMonster Graphing

# install.packages("ggplot2")
library(ggplot2)
#install.packages("ggthemes")
library(ggthemes)

#set working directory for data
setwd("/vol/v1/proj/aggregation/outputs/mr224/summary_tables/")
data=read.csv("mr224_biomasschange_byagent_crm_1990thru2010_reduced_median.csv", header = T)

scale = 9e-9

# #Rearrange data to rows instead of columns#
# new=NULL
# ###start loop from column 3 until the end
# for(i in 3:ncol(data)){
#   ####row bind to new/null with the metadata from columns 1:2, attach thier names, the append looped yearly biomass data
#   ##the data[1:2] references the columns with metadata; the (data)[i],2,5 references the year data from within the coloumn names 
#   new=rbind(new,cbind(data[1:2],as.numeric(substr(colnames(data)[i],2,5)) ,data[,i]))
#   
#                         }
# ##'new' sans the NA's; [,4] is the column reference for the new column we just created
# new=new[!is.na(new[,4]),]


#rename the dataframe
#df=new
df=data
#rename the columns
colnames(df)[2]<-"Agent"
colnames(df)[3]<-"Year"
colnames(df)[4]<-"Biomass"

#Create a separate dataset summing the yearly change in biomass from all agents
test=by(df$Biomass, df$Year,sum)
list=as.data.frame(cbind(c(test)))
Year=row.names(list)
list$Year<-Year
colnames(list)[1]="Year.Sum"

#check the values in Tg.  Joe's new numbers are kg straight up. 
#  these are the total change for each year
#Tara's numbers are kg/Ha
list$Tg=list$Year.Sum*scale

#join the yearly total change in biomass back into the original dataset
#install.packages("plyr")
library(plyr)

bigdf=join(df, list, type="left")
bigdf$AgentTg=bigdf$Biomass*scale

#Change the draw order for coloring and stacking
#Order the Agents the way you want them to be stacked for graphing
#these names need to match with what's in your CSV file, or else you'll get an NA

orderall = c("Fire", "Clearcut", "Partial Harvest", "Development",
              "Insects/Disease", "Long Slow Disturbance", 
              "Fast Disturbance", "No Agent", "Growth")

orderdown = c("Fire", "Clearcut", "Partial Harvest", "Development",
                "Insects/Disease", "Long Slow Disturbance", 
                "Fast Disturbance", "No Agent")
orderup =  c("No Agent", "Growth")

bigdf = subset(bigdf, Agent %in% orderall)
bigdf$Agent<-factor(bigdf$Agent, levels=orderall)

#have to split into two datasets; one for positive and one for negative values to make bars stack properly
bigdf1<-subset(bigdf,Biomass >=0)
bigdf2<-subset(bigdf,Biomass < 0)

#bigdf1$Agent<-factor(bigdf1$Agent, levels=orderup)
#bigdf2$Agent<-factor(bigdf2$Agent, levels=orderdown)

###COLOR SETUP FOR ALL GRAPHS###

# define colors manually
pal=palette(rainbow(9))
pal[2]="#543005" #clearcut-brown
pal[4]="#cab2d6" #development-light purple
pal[7]= "#710162" #fast disturbance-purple
pal[1]= "#d33502" #fire-red
pal[9]= "#017354" #growth-green
pal[5]= "#ef6a32" #insects/disease-orange
pal[6]= "#fbbf45" #long slow disturbance-yellow
pal[8]= "#bbb9b2" #no agent-grey
pal[3]="#3b87bd" #partial harvest-light blue

palup=palette(rainbow(2))
palup[1]= "#bbb9b2" #no agent-grey
palup[2]= "#017354" #growth-green

pal_list = c("Fire"="#d33502", "Clearcut"="#543005", "Partial Harvest"="#3b87bd", 
             "Development"="#cab2d6", "Insects/Disease"="#ef6a32", 
             "Long Slow Disturbance"="#fbbf45", "Fast Disturbance"="#710162",
             "No Agent"="#bbb9b2", "Growth"="#017354")

#####ACTUAL PLOTTING CODE!!!#########

setwd("/vol/v1/proj/aggregation/figs/")
yrange = c(-10,10)
xrange = c(1991,2010)
ranges=data.frame(xrange,yrange)
colnames(ranges)[1] = "X"
colnames(ranges)[2] = "Y"

#x11()

orderdf1 <-bigdf1[order(bigdf1$ORDER),]
orderdf2 <-bigdf2[order(bigdf2$ORDER),]

p<-ggplot()+
  geom_bar(aes(Year, AgentTg, fill=Agent, order=Agent), orderdf2, stat = "identity", position = "stack")+
  geom_bar(aes(Year, AgentTg, fill=Agent, order=Agent), orderdf1, stat = "identity", position = "stack")+
  ylab("Total delta biomass (Tg)")+
  xlab("Year")+
  geom_abline(intercept=0, slope=0, colour="black", size=1)+
  scale_fill_manual(values=pal_list, breaks=orderall, guide=guide_legend(reverse=TRUE))+
  geom_rangeframe(data=ranges, mapping=aes(x=X, y=Y))+
  theme_tufte(base_size=20, base_family="BemboStd")+
  theme(axis.title.x=element_text(size=rel(2)))+
  theme(axis.title.y=element_text(size=rel(2)))+
  theme(axis.text.x=element_text(size=rel(1.5), vjust=0.45))+
  theme(axis.text.y=element_text(size=rel(1.5), vjust=0.45))+
  theme(legend.title=element_text(size=rel(1.25)))+
  theme(legend.text=element_text(size=rel(1)))+
  scale_y_continuous(limits = yrange)+
  scale_x_continuous(limits= xrange, breaks=seq(1990,2010,5))

#p
#pdf("mr224_crm_deltabiomass_totalsum_barchart_cleaned.pdf")
plot(p)
#dev.off()

#####################
#To put graphs in a new window on linux, type in x11() first; 
#all plots will go to this window until you either close it or call a second window from x11()


#This makes a separate graph for each agent
#x11()
#z=ggplot(data=bigdf1,aes(factor(Year),Biomass*scale,fill=Agent))+ 
#        geom_bar(stat = "identity")+
#        geom_bar(aes(factor(Year),Biomass*scale,fill=Agent),bigdf2,stat = "identity",position = "identity")+
#        facet_wrap(~Agent)+ylab("Total delta biomass(Mg)")+xlab("Year")+scale_fill_manual(values=pal)
#z
#pdf("mr224_crm_deltabiomass_totalsum_plotperagent_barchart.pdf")
#plot(z)
#dev.off()


#####################
#Net gain/loss by year with the individual data overlayed
#x11()
#q<-ggplot(list,aes(factor(Year),Year.Sum*9e-6))+geom_bar(stat="identity")+xlab("Year")+ylab("Total delta biomass(Mg)")+
#        geom_bar(aes(factor(Year),Biomass*9e-6,fill=Agent,order=Agent),bigdf,stat = "identity",position = "dodge")+scale_fill_manual(values=pal)+
#        geom_abline(intercept=0, slope=0, colour="black", size=1.75)
#q
#pdf("mr224_crm_deltabiomass_netgainloss.pdf")
#plot(q)
#dev.off()

#To save a pdf, I always just close any x11 windows I have open and plot it within rstudio.  
#Above the graph should be a button for exporting a pdf, I usually use letter size



#NOT USED BELOW#
##############
#NOT USED BELOW#

#Though when bigdf1 and bigdf2 were created they inherited the ordering of factors, they behave oddly
#because not all change agents are present in each dataset
#bigdf2$Agent<-factor(bigdf2$Agent, levels=c("Fire","No Agent","Clearcut", "Development", "Partial Harvest",
#                                         "Insect/Disease", "Greatest Disturbance; Unfiltered", "Road", "False Change", "Unknown Agent", "Water", 
#                                        "Debris Flow", "Other", "MPB-29", "MPB-239", "WSB-29", "WSB-239", 
#                                       "Longest Disturbance; Unfiltered"))
#order=c("Fire","No Agent", "Wetness Longest Recovery 2; Unfiltered","Clearcut", "Development", "Partial Harvest",
#    "Insect/Disease", "Greatest Disturbance; Unfiltered", "Road", "False Change", "Unknown Agent", "Water", 
#   "Debris Flow", "Other", "MPB-29", "MPB-239", "WSB-29", "WSB-239", 
#  "Longest Disturbance; Unfiltered")
#unique(bigdf2$Agent



#qplot(factor(Year),Year.Sum/1000000000,data=bigdf, geom="bar",stat = "identity",xlab= "Year",ylab = "Total delta biomass(Gg)")
#x11()
#qplot(factor(Year),Biomass/1000000,data=bigdf, geom="bar",stat = "identity",fill=factor(Agent),facets= ~Agent) 
#qplot(factor(Year),Year.Sum/1000000000,data=bigdf, geom="bar",stat = "identity",xlab= "Year",ylab = "Total delta biomass(Gg)")+
#geom_text(aes(x=factor(Year),y=Biomass,label=Biomass))+
# geom_abline(intercept=0, slope=0, colour="black", size=1.5)

#q<-ggplot(bigdf,aes(factor(Year),Year.Sum/1000000),xlab= "Year",ylab = "Total delta biomass(Gg)")+geom_bar(stat="identity")
#q+geom_bar(aes(factor(Year),Biomass/1000000000,fill=Agent),bigdf,stat = "identity",position = "identity")+geom_abline(intercept=0, slope=0, colour="black", size=1.5)

#qplot(factor(Year),Biomass,data=df, geom="bar",stat = "identity",fill=factor(Agent))
#qplot(factor(Year),Biomass,data=df, geom="bar",stat = "identity",fill=factor(Agent),facets= ~Agent)


# p<- ggplot(bigdf1, aes(factor(Year),Biomass,fill=factor(Agent)))+geom_bar(stat="identity",position="stack")
# r<-p+geom_bar(aes(factor(Year),Biomass,fill=factor(Agent)),bigdf2,stat = "identity",position = "stack")+ylab("Total delta biomass(Mg)")+xlab("Year")
# r
# #rr+geom_bar(data=list,aes(factor(Year),Year.Sum,alpha=.1),stat = "identity",position = "identity",fill="white",colour="black")
# 
# #ggplot(list,aes(factor(Year),Year.Sum/1000000))+geom_bar(stat="identity")
#p<-ggplot()+geom_bar(aes(factor(Year),Biomass/1000000,fill=factor(Agent)),bigdf2,stat = "identity",position = "stack")

#p<-ggplot(bigdf2, aes(factor(Year),Biomass/1000000,fill=factor(Agent)))+geom_bar(stat="identity",position="stack")

#qplot(factor(Year),Biomass/1000000,data=df, geom="bar",stat = "identity",fill=factor(Agent), label,margins=T)+
#geom_text(aes(x=factor(Year),y=Biomass,label=Biomass))+
#  geom_abline(intercept=0, slope=0, colour="black", size=1.5)

#library(RColorBrewer)
#display.brewer.all()
#brewer.pal.info()
#display.brewer.all()


  
#range(bigdf$Year.Sum)

