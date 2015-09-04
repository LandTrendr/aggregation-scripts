##CMonster Graphing

# install.packages("ggplot2")
library(ggplot2)

#set working directory for old data

# setwd("/projectnb/trenders/proj/aggregation/outputs/mr224/summary_tables/")
# data2=read.csv("all.csv", header = T)

#set working directory for new data
setwd("/projectnb/trenders/proj/aggregation/outputs/mr224/summary_tables/")
#data=read.csv("mr224_median_biomass_change_by_agent_year_REK.csv", header = T)
data=read.csv("mr224_agent_hectares_summary.csv", header = T)

########################
#NOT USED#
#data2=read.csv("mr224_summary.csv", header = T)
#data3=read.csv("mr224_summary_update.csv", header = T)
#row.names(data)<-data$Agent
#data[,3:22]=as.numeric(as.character(data[,3:22]))
#qplot(data[,3:22])
#plot(as.integer(as.character(data[20,3:22])),as.integer(data[1:19,3:22]))
#data[20,]<-rbind(c(NA,NA,"1991", "1992", "1993", "1994", "1995", "1996", "1997", "1998", 
#                          "1999", "2000", "2001", "2002", "2003", "2004", "2005", "2006", 
#                          "2007", "2008", "2009", "2010"))
#names=paste0(1991:2010)  
#new=NULL
###start loop from column 15 until the end
#for(i in 15:ncol(data)){
  ####row bind to new/null with the metadata from columns 1:14, attach thier names, the append looped data
#  new=rbind(new,cbind(data[1:14],as.numeric(substr(colnames(data)[i],2,5)) ,data[,i]))

#}
##new=new sans the NA's
#new=new[!is.na(new[,16]),]
###############################
#Rearrange data to rows instead of columns#
new=NULL
###start loop from column 3 until the end
for(i in 3:ncol(data)){
  ####row bind to new/null with the metadata from columns 1:2, attach thier names, the append looped yearly biomass data
  ##the data[1:2] references the columns with metadata; the (data)[i],2,5 references the year data from within the coloumn names 
  new=rbind(new,cbind(data[1:2],as.numeric(substr(colnames(data)[i],2,5)) ,data[,i]))
  
                        }
##'new' sans the NA's; [,4] is the column reference for the new column we just created
new=new[!is.na(new[,4]),]


#rename the dataframe
df=new
#rename the columns
colnames(df)[2]<-"Agent"
colnames(df)[3]<-"Year"
colnames(df)[4]<-"Area"

#Create a separate dataset summing the yearly change in biomass from all agents
test=by(df$Area, df$Year,sum)
list=as.data.frame(cbind(c(test)))
Year=row.names(list)
list$Year<-Year
colnames(list)[1]="Year.Sum"

#check the values in Tg.  Joe's new numbers are kg straight up. 
#  these are the total change for each year

# list$Tg=list$Year.Sum/1000000000

#join the yearly total change in biomass back into the original dataset
#install.packages("plyr")
library(plyr)
print("here")
bigdf=join(df, list, type="left")

print("there")


#Change the draw order for coloring and stacking
#Order the Agents the way you want them to be stacked for graphing
# these names need to match with what's in your CSV file, or else you'll get an NA
print(bigdf$Agent)
# bigdf$Agent<-factor(bigdf$Agent, levels=c("Fire","No Agent", "Growth", "Clearcut", "Development", "Partial Harvest",
#                                           "Insect/Disease", "Greatest Disturbance", "Road", "False Change", "Unknown Agent", "Water", 
#                                           "Debris Flow", "Other", "MPB-29", "MPB-239", "WSB-29", "WSB-239", 
#                                           "Longest Disturbance"))
bigdf$Agent<-factor(bigdf$Agent, levels=c("Fire", "Growth", "Clearcut", "Development", "Partial Harvest",
                                          "Insect/Disease", "Greatest Disturbance", "Road", "False Change", "Unknown Agent", "Water", 
                                          "Debris Flow", "Other", "MPB-29", "MPB-239", "WSB-29", "WSB-239", 
                                          "Longest Disturbance"))

#have to split into two datasets; one for positive and one for negative values to make bars stack properly
# bigdf1<-subset(bigdf,Biomass >=0)
# bigdf2<-subset(bigdf,Biomass < 0)

print(bigdf)

#Creates a list that will be ordered alphabetically, so that the colors can be matched accordingly, shouldn't ever need to change
# order=cbind(sort(c("Fire","No Agent", "Growth", "Clearcut", "Development", "Partial Harvest",
#                    "Insect/Disease", "Greatest Disturbance", "Road", "False Change", "Unknown Agent", "Water", 
#                    "Debris Flow", "Other", "MPB-29", "MPB-239", "WSB-29", "WSB-239", 
#                    "Longest Disturbance")))
# order=cbind(c("Fire","No Agent", "Growth", "Clearcut", "Development", "Partial Harvest",
#                    "Insect/Disease", "Greatest Disturbance", "Road", "False Change", "Unknown Agent", "Water", 
#                    "Debris Flow", "Other", "MPB-29", "MPB-239", "WSB-29", "WSB-239", 
#                    "Longest Disturbance"))
order=cbind(c("Fire", "Growth", "Clearcut", "Development", "Partial Harvest",
                   "Insect/Disease", "Greatest Disturbance", "Road", "False Change", "Unknown Agent", "Water", 
                   "Debris Flow", "Other", "MPB-29", "MPB-239", "WSB-29", "WSB-239", 
                   "Longest Disturbance"))


###COLOR SETUP FOR ALL GRAPHS###
      #Make up a 19 color rainbow palette :)
      pal=palette(rainbow(19))
      #graph it to gauge your feelings about it
      #barplot(rep(1,19),col=pal,yaxt="n")
      
      #covert to RGB colors with a max of 255
      #rgbcols=col2rgb(pal)
      #color<-row.names(rgbcols)
      #rgbcols=cbind(color,rgbcols)
      
      #This will lauch an interactive editor where you can change the RGB colors to your liking; they will map *alphabetically* with the Agent classes;
      #you can view such an alphabetical agent list by typing order or View(order) in the console, or clicking on it the environment
      #fix(rgbcols)
      
      #Makes sure to save this file as it is currently just a temp file in the current environment
      #write.csv(rgbcols,"color_palette.csv",row.names=F)
      
      #retrive csv if necessary -> 
      #rgbcols=read.csv("color_palette.csv")
      
      #covert back into the format ggplot can read; the 190 value here is alpha,       
      #which softens the colors with transparency, setting it to 255 will elimate this is desired
      #col.scheme=rgb(rgbcols[1,2:20],rgbcols[2,2:20],rgbcols[3,2:20],190,maxColorValue = 255)
insectcolor = "#FF9955"
pal[1]="#4444CC"  #clearcut
pal[2]="#883322"  #debris flow
pal[3]="#FFFF22"  #development
pal[4]="#DDDDDD"  #false change
pal[5]="#EE0000"  #fire
pal[6]="#6666DD"  #greatest disturbance
pal[7]="#33CC33"  #growth
pal[8]=insectcolor  #insect/disease
pal[9]=insectcolor  #longest disturbance
pal[10]=insectcolor  #MPB-239
pal[11]=insectcolor  #MPB-29
pal[12]="#FFDDDD"  #No Agent
pal[13]="#DDDDDD"  #Other
pal[14]="#5588FF"  #Partial harvest
pal[15]="#000000"  #Road
pal[16]="#dddddd"  #Unknown agent
pal[17]="#000099"  #Water
pal[18]=insectcolor  #WSB-239
pal[19]=insectcolor #wsb-29





#####ACTUAL PLOTTING CODE!!!#########
setwd("/projectnb/trenders/proj/aggregation/figs/")
      p<-ggplot()+
           geom_bar(aes(factor(Year), Area, fill=Agent, order=Agent), bigdf, stat = "identity", position = "stack")+
           # geom_bar(aes(factor(Year), Biomass/1000000000,fill=Agent, order=Agent),bigdf2, stat = "identity", position = "stack")+
           #geom_bar(aes(factor(Year), Year.Sum/1000000000,alpha=0.), data=list, stat = "identity", position = "identity",fill="black", colour="black") +
           #geom_bar(aes(factor(Year), Year.Sum/1000000000), data=list, stat="identity", position="identity", solid=FALSE)+ 
          #ylab("Total delta biomass(Mg)")+xlab("Year")+geom_abline(intercept=0, slope=0, colour="black", size=1)+scale_fill_manual(values=col.scheme)
           ylab("Total Area (Ha)")+
          xlab("Year")+
          geom_abline(intercept=0, slope=0, colour="black", size=1)+
          scale_fill_manual(values=pal)
p<-p+theme(axis.title.x=element_text(size=rel(2)))
p<-p+theme(axis.title.y=element_text(size=rel(2)))
p<-p+theme(axis.text.x=element_text(angle=90, size=rel(2), vjust=0.45))
p
pdf("mr224_area_barchart.pdf")
plot(p)
dev.off()

#####################
# #To put graphs in a new window on linux, type in x11() first; 
# #all plots will go to this window until you either close it or call a second window from x11()


# #This makes a separate graph for each agent
# x11()
# z=ggplot(data=bigdf1,aes(factor(Year),Biomass/1000000,fill=Agent))+ 
#         geom_bar(stat = "identity")+
#         geom_bar(aes(factor(Year),Biomass/1000000,fill=Agent),bigdf2,stat = "identity",position = "identity")+
#         facet_wrap(~Agent)+ylab("Total delta biomass(Mg)")+xlab("Year")+scale_fill_manual(values=pal)
# z
# pdf("mr224_combined_deltabiomass_totalsum_plotperagent_barchart.pdf")
# plot(z)
# dev.off()


# #####################
# #Net gain/loss by year with the individual data overlayed
# x11()
# q<-ggplot(list,aes(factor(Year),Year.Sum/1000000))+geom_bar(stat="identity")+xlab("Year")+ylab("Total delta biomass(Mg)")+
#          geom_bar(aes(factor(Year),Biomass/1000000,fill=Agent,order=Agent),bigdf,stat = "identity",position = "dodge")+scale_fill_manual(values=pal)+
#          geom_abline(intercept=0, slope=0, colour="black", size=1.75)
# q
# pdf("mr224_combined_deltabiomass_netgainloss.pdf")
# plot(q)
# dev.off()


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

