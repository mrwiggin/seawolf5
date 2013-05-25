from __future__ import division
import math
import cv
import svr
from base import VisionEntity
import libvision
from sw3.util import circular_average, circular_range
#import msvcrt
import random




class Bin(object):
    bin_id = 0
    '''an imaged bin'''
    def __init__(self, corner_a,corner_b,corner_c, corner_d):
        rng = cv.RNG()
        self.midx = rect_midpointx(corner_a,corner_b,corner_c,corner_d)
        self.midy = rect_midpointy(corner_a,corner_b,corner_c,corner_d)
        self.corner1 = corner_a
        self.corner2 = corner_b
        self.corner3 = corner_c
        self.corner4 = corner_d
        #locx and locy are relative locations of corners when compared to other corners of the same rectangle
        self.corner1_locx = self.corner1[0] - self.corner2[0]
        self.corner1_locy = self.corner1[1] - self.corner2[1]
        self.corner2_locx = self.corner2[0] - self.corner1[0]
        self.corner2_locy = self.corner2[1] - self.corner1[1]
        self.corner3_locx = self.corner3[0] - self.corner1[0]
        self.corner3_locy = self.corner3[1] - self.corner1[1]        
        self.corner4_locx = self.corner4[0] - self.corner1[0]
        self.corner4_locy = self.corner4[1] - self.corner1[1]
        #angle is found according to short side
        if line_distance(corner_a,corner_c)< line_distance(corner_a, corner_b):
                self.angle = -angle_between_lines(line_slope(corner_a,corner_c), 0)
        else:
                self.angle = -angle_between_lines(line_slope(corner_a,corner_b), 0)
        self.id = 0   #id identifies which bin your looking at
        self.last_seen = 2 #how recently you have seen this bin
        self.seencount = 1 #how many times you have seen this bin (if you see it enough it becomes confirmed)
        r = int(cv.RandReal(rng)*255)
        g = int(cv.RandReal(rng)*255)
        b = int(cv.RandReal(rng)*255)
        self.debug_color = cv.RGB(r,g,b)
        self.object = random.choice(["A", "B", "C", "D"])

def line_distance(corner_a, corner_b):
        distance = math.sqrt((corner_b[0]-corner_a[0])**2 + (corner_b[1]-corner_a[1])**2)
        return distance

def line_slope(corner_a, corner_b):
        if corner_a[0] != corner_b[0]:
                slope = (corner_b[1]-corner_a[1])/(corner_b[0]-corner_a[0])
                return slope

def angle_between_lines(slope_a, slope_b):
    if slope_a != None and slope_b != None and (1+slope_a*slope_b) != 0:
        angle = math.atan((slope_a - slope_b)/(1+slope_a*slope_b))
        return angle
    else: 
        angle = 0
        return angle

def midpoint(corner_a, corner_b):
        midpoint_x = (corner_b[0] - corner_a[0])/2+corner_a[0]
        midpoint_y = (corner_b[1] - corner_a[1])/2+corner_a[1]
        return [midpoint_x, midpoint_y]

def midpointx(corner_a, corner_b):
        midpoint_x = (corner_b[0] - corner_a[0])/2+corner_a[0]
        return midpoint_x

def midpointy(corner_a, corner_b):
        midpoint_y = (corner_b[1] - corner_a[1])/2+corner_a[1]
        return midpoint_y

def rect_midpointx(corner_a,corner_b,corner_c,corner_d):
        midpoint_x = (corner_a[0]+corner_b[0]+corner_c[0]+corner_d[0])/4
        return midpoint_x

def rect_midpointy(corner_a,corner_b,corner_c,corner_d):
        midpoint_y = (corner_a[1]+corner_b[1]+corner_c[1]+corner_d[1])/4
        return midpoint_y


                



class BinsCornerEntity(VisionEntity):
    
   

    def init(self):

        #Adaptive threshold parameters
        self.adaptive_thresh_blocksize = 19
        self.adaptive_thresh = 12

        #Good features parameters
        self.max_corners = 18
        self.quality_level = .75
        self.min_distance = 40
        self.good_features_blocksize = 24
        
        #min and max angle in order to only accept rectangles
        self.angle_min = math.pi/2-.15
        self.angle_max = math.pi/2+.15
        self.angle_min2 = math.pi/2-.15
        self.angle_max2 = math.pi/2+.15

        #how close the sizes of parallel lines of a bin must be to eachother
        self.size_threshold = 40
        #How close to the ideal 2:1 ratio the bin sides must be
        self.ratio_threshold = .7
        
        #How far a bin may move and still be considered the same bin
        self.MaxTrans = 40

        #Minimum number the seencount can be before the bin is lost
        self.last_seen_thresh = 0
        #How many times a bin must be seen to be accepted as a confirmed bin
        self.min_seencount = 5
 
        #How close the perimeter of a bin must be when compared to the perimeter of other bins
        self.perimeter_threshold = 0.08


        self.corners = []
        self.candidates = []
        self.confirmed  = []
        self.new = []
        self.angles = []

        
        




    def process_frame(self, frame):
        self.debug_frame = cv.CreateImage(cv.GetSize(frame),8,3)
        cv.Copy(frame, self.debug_frame)
        cv.Smooth(frame, frame, cv.CV_MEDIAN, 7, 7)

        # Set binary image to have saturation channel
        hsv = cv.CreateImage(cv.GetSize(frame), 8, 3)
        binary = cv.CreateImage(cv.GetSize(frame), 8, 1)
        cv.CvtColor(frame, hsv, cv.CV_BGR2HSV)
        cv.SetImageCOI(hsv, 3)
        cv.Copy(hsv, binary)
        cv.SetImageCOI(hsv, 0)

        
        #Adaptive Threshold
        cv.AdaptiveThreshold(binary, binary,
            255,
            cv.CV_ADAPTIVE_THRESH_MEAN_C,
            cv.CV_THRESH_BINARY_INV,
            self.adaptive_thresh_blocksize,
            self.adaptive_thresh,
        )

        # Morphology
        kernel = cv.CreateStructuringElementEx(5, 5, 3, 3, cv.CV_SHAPE_ELLIPSE)
        cv.Erode(binary, binary, kernel, 1)
        cv.Dilate(binary, binary, kernel, 1)
        
   
        cv.CvtColor(binary,self.debug_frame, cv.CV_GRAY2RGB)
        
        
        
        #Find Corners
        temp1 = cv.CreateImage(cv.GetSize(frame), 8, 1)
        temp2 = cv.CreateImage(cv.GetSize(frame), 8, 1)
        self.corners = cv.GoodFeaturesToTrack(binary, temp1, temp2, self.max_corners, self.quality_level, self.min_distance, None, self.good_features_blocksize, 0, 0.4) 
        
        #Display Corners
        for corner in self.corners:
                corner_color = (0,0,255)
                text_color = (0, 255, 0)
                font = cv.InitFont(cv.CV_FONT_HERSHEY_SIMPLEX, .6, .6, 0, 1, 1)
                cv.Circle(self.debug_frame, (int(corner[0]),int(corner[1])), 15, corner_color, 2,8,0)
                
        

        #Find Candidates

        for corner1 in self.corners:
                for corner2 in self.corners:
                        for corner3 in self.corners:
                                for corner4 in self.corners:
                                        #Checks that corners are not the same and are in the proper orientation
                                        if corner4[0] != corner3[0] and corner4[0] != corner2[0] and corner4[0] != corner1[0] and corner3[0] != corner2[0] and corner3[0] != corner1[0] and corner2[0] != corner1[0] and corner4[1] != corner3[1] and corner4[1] != corner2[1] and corner4[1] != corner1[1] and corner3[1] != corner2[1] and corner3[1] != corner1[1] and corner2[1] != corner1[1] and corner2[0]>=corner3[0] and corner1[1]>=corner4[1] and corner2[0]>=corner1[0]:
                                                #Checks that the side ratios are correct
                                                if math.fabs(line_distance(corner1,corner3) - line_distance(corner2,corner4)) < self.size_threshold and math.fabs(line_distance(corner1,corner2) - line_distance(corner3,corner4)) < self.size_threshold and math.fabs(line_distance(corner1,corner3)/line_distance(corner1,corner2)) < self.ratio_threshold or math.fabs(line_distance(corner1,corner2)/line_distance(corner1,corner3)) < self.ratio_threshold:
                                                        #Checks that angles are roughly 90 degrees
                                                        if math.fabs(angle_between_lines(line_slope(corner1, corner2),line_slope(corner2,corner4) ))> self.angle_min and math.fabs(angle_between_lines(line_slope(corner1, corner2),line_slope(corner2,corner4))) < self.angle_max:
                                                                if math.fabs(angle_between_lines(line_slope(corner1, corner3),line_slope(corner3,corner4) ))> self.angle_min2 and math.fabs(angle_between_lines(line_slope(corner1, corner3),line_slope(corner3,corner4))) < self.angle_max2:
                                                                        new_bin = Bin(corner1,corner2,corner3,corner4)
                                                                        self.match_bins(new_bin)
        self.sort_bins()                                                                
        svr.debug("Bins", self.debug_frame)
                
        #Output bins
        self.output.bins = self.confirmed
        anglesum = 0
        for bins in self.output.bins:
            bins.theta = (bins.midx - frame.width/2) * 37 / (frame.width/2)
            bins.phi = -1 * (bins.midy - frame.height/2) * 36 / (frame.height/2)
            bins.shape = bins.object
            anglesum += bins.angle
           # bins.orientation = bins.angle
        if len(self.output.bins) > 0:           
            self.output.orientation = anglesum/len(self.output.bins)
        else:
            self.output.orientation = None
        self.return_output()
        

    def match_bins(self, target):
                existing = 0
                #update if candidate
                for candidate in self.candidates:
                        if math.fabs(target.midx-candidate.midx) < self.MaxTrans and math.fabs(target.midy-candidate.midy) < self.MaxTrans and target.id != candidate.id:
                                candidate.midx = target.midx
                                candidate.midy = target.midy
                                candidate.corner1 = target.corner1
                                candidate.corner2 = target.corner2
                                candidate.corner3 = target.corner3
                                candidate.corner4 = target.corner4
                                candidate.angle = target.angle
                                candidate.corner1_locx = candidate.corner1[0] - candidate.corner2[0]
                                candidate.corner1_locy = candidate.corner1[1] - candidate.corner2[1]
                                candidate.corner2_locx = candidate.corner2[0] - candidate.corner1[0]
                                candidate.corner2_locy = candidate.corner2[1] - candidate.corner1[1]
                                candidate.corner3_locx = candidate.corner3[0] - candidate.corner1[0]
                                candidate.corner3_locy = candidate.corner3[1] - candidate.corner1[1]        
                                candidate.corner4_locx = candidate.corner4[0] - candidate.corner1[0]
                                candidate.corner4_locy = candidate.corner4[1] - candidate.corner1[1]
                                if candidate.last_seen < 20:
                                        candidate.last_seen +=3
                                candidate.seencount +=1
                                existing = 1
                #update if confirmed
                for confirmed in self.confirmed:
                        for confirmed2 in self.confirmed:
                                if confirmed.midx == confirmed2.midx and confirmed.midy == confirmed2.midy and confirmed.id != confirmed2.id:
                                        if confirmed.id < confirmed2.id:
                                                self.confirmed.remove(confirmed2)


                        if math.fabs(target.midx-confirmed.midx) < self.MaxTrans and math.fabs(target.midy-confirmed.midy) < self.MaxTrans and target.id != confirmed.id:
                                confirmed.midx = target.midx
                                confirmed.midy = target.midy
                                confirmed.corner1 = target.corner1
                                confirmed.corner2 = target.corner2
                                confirmed.corner3 = target.corner3
                                confirmed.corner4 = target.corner4
                                confirmed.angle = target.angle
                                if confirmed.last_seen < 20:
                                        confirmed.last_seen +=3
                                confirmed.seencount +=1
                                existing = 1
                if existing == 0:
                        print "found candidate"
                        target.id = Bin.bin_id
                        Bin.bin_id += 1
                        self.candidates.append(target)




    def sort_bins(self):
                #promote candidate to confirmed if seen enough times, if it hasn't been seen, delete the bin
                for candidate in self.candidates:

                        candidate.last_seen -= 1
                        if candidate.last_seen < self.last_seen_thresh:
                                self.candidates.remove(candidate) 
                                print "lost"
                                continue
                        if candidate.seencount > self.min_seencount:
                                self.confirmed.append(candidate)
                                self.candidates.remove(candidate)
                                print "confirmed"
                                continue

                self.min_perimeter = 500000        
                self.angles = []
                for confirmed in self.confirmed:
                        if 0 < line_distance(confirmed.corner1,confirmed.corner3)*2 + line_distance(confirmed.corner1,confirmed.corner2)*2 < self.min_perimeter:         
                                self.min_perimeter = line_distance(confirmed.corner1,confirmed.corner3)*2 + line_distance(confirmed.corner1,confirmed.corner2)*2
                        #print confirmed.angle/math.pi*180
                        self.angles.append(cv.Round(confirmed.angle/math.pi*180/10)*10)

                #compare perimeter of existing bins. If a bin is too much bigger than the others, it is deleted. This is done to get rid of bins found based of 3 bins
                for confirmed in self.confirmed:
                        if math.fabs(line_distance(confirmed.corner1,confirmed.corner3)*2 + math.fabs(line_distance(confirmed.corner1,confirmed.corner2)*2) - self.min_perimeter)>self.min_perimeter*self.perimeter_threshold and line_distance(confirmed.corner1,confirmed.corner3)*2 + line_distance(confirmed.corner1,confirmed.corner2)*2 > self.min_perimeter:
                                print "perimeter error (this is a good thing)"        
                                print math.fabs(line_distance(confirmed.corner1,confirmed.corner3)*2 + math.fabs(line_distance(confirmed.corner1,confirmed.corner2)*2) - self.min_perimeter), "is greater than", self.min_perimeter*self.perimeter_threshold
                                print "yay?"

                                confirmed.last_seen -= 5

                                continue

                        
                        confirmed.last_seen -= 1
                        if confirmed.last_seen < self.last_seen_thresh:
                                self.confirmed.remove(confirmed) 
                                print "lost confirmed"
                                continue
                        #draw bins
                        line_color = (confirmed.corner1[1]/2,confirmed.corner2[1]/2,confirmed.corner4[1]/2)
                        cv.Circle(self.debug_frame, (int(confirmed.midx),int(confirmed.midy)), 15, line_color, 2,8,0)
                        pt1 = (cv.Round(confirmed.corner1[0]), cv.Round(confirmed.corner1[1]))
                        pt2 = (cv.Round(confirmed.corner2[0]), cv.Round(confirmed.corner2[1]))
                        cv.Line(self.debug_frame, pt1, pt2, line_color, 1, cv.CV_AA, 0)
                        pt2 = (cv.Round(confirmed.corner2[0]), cv.Round(confirmed.corner2[1]))
                        pt4 = (cv.Round(confirmed.corner4[0]), cv.Round(confirmed.corner4[1]))
                        pt3 = (cv.Round(confirmed.corner3[0]),cv.Round(confirmed.corner3[1]))
                        cv.Line(self.debug_frame, pt2, pt4, line_color, 1, cv.CV_AA, 0)
                        cv.Line(self.debug_frame, pt3,pt4, line_color, 1, cv.CV_AA, 0)
                        cv.Line(self.debug_frame, pt1,pt3, line_color, 1, cv.CV_AA, 0)
                        font = cv.InitFont(cv.CV_FONT_HERSHEY_SIMPLEX, .6, .6, 0, 1, 1)
                        text_color = (0, 255, 0)
                        #print id and last_seen by each bin
                        cv.PutText(self.debug_frame, str(confirmed.id), (int(confirmed.midx),int(confirmed.midy)), font, confirmed.debug_color)
                        cv.PutText(self.debug_frame, str(confirmed.last_seen), (int(confirmed.midx-20),int(confirmed.midy-20)), font, confirmed.debug_color)


#TODO Lower how much it gets from seeing corners to reduce things. Add variable for max last_seen instead of stating in code. Delete lost[] code or archive useful parts. fix perimeter error. get rid of bbb's. Fix integration of flux capacitors. Reduce interference from time lords. Prevent the rise of skynet. Speed up the processes so they can make the kessler run in under 12 parsecs. Go plaid in ludicrous speed. (NOTE: It's a Unix System, I know this). 



#Ideas: lower maxtrans, fix numerous bins sharing the same spot.
