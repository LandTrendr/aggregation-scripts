##CMonster Graphing - Uncertainty by Agent

# install.packages("ggplot2")
library(ggplot2)
#install.packages("plyr")
library(plyr)
#install.packages("ggthemes")
library(ggthemes)
#install.packages("extrafont")
library(extrafont)
#install.packages("grid")
#library(grid)

#set working directory for new data
setwd("/vol/v1/proj/aggregation/outputs/mr224/summary_tables/")

#read dataset
data=read.csv("mr224_biomasschange_byagent_crm_1990thru2010_reduced_uncertainty.csv", header = T)

#rename the columns
colnames(data)[4]<-"Median"
colnames(data)[5]<-"Max"
colnames(data)[6]<-"Min"

#scale to Terabytes
data$Median<-data$Median/(11.1111e7)
data$Max<-data$Max/(11.1111e7)
data$Min<-data$Min/(11.1111e7)

#specify agents to graph
graphagents<-c("Fire", "Clearcut", "Insects/Disease", "Partial Harvest")

#define ranges
yrange = c(-5,0.5)
xrange = c(1991,2010)
ranges=data.frame(xrange,yrange)
colnames(ranges)[1] = "X"
colnames(ranges)[2] = "Y"

#function to define a plot
defineplot <- function(agentname, xaxislabel, yaxislabel) {
  h<-ggplot(subset(data, AGENT==agentname), aes(x=YEAR))+
    geom_ribbon(aes(ymin=Min, ymax=Max), fill="lightgrey")+
    geom_line(aes(y=Min), lwd=.5, lty=1, col="lightgrey")+
    geom_line(aes(y=Max), lwd=.5, lty=1, col="lightgrey")+
    geom_line(aes(y=Median), lwd=.75, lty=1, col="black")+
    #geom_line(aes(y=Min), linetype="l", pch=16, lwd=.5, lty=1, col="lightgrey")+
    #geom_line(aes(y=Max), linetype="l", pch=16, lwd=.5, lty=1, col="lightgrey")+
    #geom_line(aes(y=Median), type="l", pch=16, lwd=.75, lty=1, col="black")+
    ggtitle(agentname)+
    #theme(axis.text.x=element_text(angle=90.,size=rel(2),vjust=0.45))+
    theme(axis.text.x=element_text(size=rel(2),vjust=0.45))+
    theme(axis.text.y=element_text(size=rel(2)))+
    theme(plot.title=element_text(lineheight=0.7, size=rel(2)))+
    scale_y_continuous(limits=yrange, breaks=seq(-5,5,1))+
    scale_x_continuous(limits=c(1991,2010), breaks=seq(1990,2010,5))+
    #geom_rangeframe(aes(y=Min))+
    geom_rangeframe(data=ranges, mapping=aes(x=X, y=Y))+
    theme_tufte(base_size=20, base_family="BemboStd")
  
  if (yaxislabel) {
    h<-h+ylab("Change in Biomass (Tg)")
    h<-h+theme(axis.title.y=element_text(size=rel(1), lineheight=10))
  }
  else {
    h<-h+ylab("")
  }
  
  if (xaxislabel){
    h<-h+xlab("Year")
    h<-h+theme(axis.title.x=element_text(size=rel(1), lineheight=10))
  }
  else {
    h<-h+xlab("")
  }
  
  return(h)
}

# Multiple plot function
#
# ggplot objects can be passed in ..., or to plotlist (as a list of ggplot objects)
# - cols:   Number of columns in layout
# - layout: A matrix specifying the layout. If present, 'cols' is ignored.
#
# If the layout is something like matrix(c(1,2,3,3), nrow=2, byrow=TRUE),
# then plot 1 will go in the upper left, 2 will go in the upper right, and
# 3 will go all the way across the bottom.
#
multiplot <- function(..., plotlist=NULL, file, cols=1, layout=NULL) {
  library(grid)
  
  # Make a list from the ... arguments and plotlist
  plots <- c(list(...), plotlist)
  
  numPlots = length(plots)
  
  # If layout is NULL, then use 'cols' to determine layout
  if (is.null(layout)) {
    # Make the panel
    # ncol: Number of columns of plots
    # nrow: Number of rows needed, calculated from # of cols
    layout <- matrix(seq(1, cols * ceiling(numPlots/cols)),
                     ncol = cols, nrow = ceiling(numPlots/cols))
  }
  
  if (numPlots==1) {
    print(plots[[1]])
    
  } else {
    # Set up the page
    grid.newpage()
    pushViewport(viewport(layout = grid.layout(nrow(layout), ncol(layout))))
    
    # Make each plot, in the correct location
    for (i in 1:numPlots) {
      # Get the i,j matrix positions of the regions that contain this subplot
      matchidx <- as.data.frame(which(layout == i, arr.ind = TRUE))
      
      print(plots[[i]], vp = viewport(layout.pos.row = matchidx$row,
                                      layout.pos.col = matchidx$col))
    }
  }
}


h1 = defineplot(graphagents[1], FALSE, TRUE)
h2 = defineplot(graphagents[2], TRUE, TRUE)
h3 = defineplot(graphagents[3], FALSE, FALSE)
h4 = defineplot(graphagents[4], TRUE, FALSE)

#x11()
#pdf("uncertaintygraph_test.pdf")
multiplot(h1, h2, h3, h4, cols=2)
#dev.off()



