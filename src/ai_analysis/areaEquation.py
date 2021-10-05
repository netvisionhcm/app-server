class areaEquation:
    def __init__(self, cameraID, area_name, warning, danger):
        self.cameraID = cameraID
        self.area_name = area_name
        self.warning = warning
        self.danger = danger
    
    def resetArea(self, warning, danger):
        self.setwarning(warning)
        self.setdanger(danger)
        
    def setAreaname(self, area_name):
        self.area_name = area_name
    
    def setWarning(self, warning):
        self.warning = warning
    
    def setDanger(self, danger):
        self.danger = danger
        
    def crossCheking(self, point, areas):
        checkSum = 0
        i = 0
        while i < len(areas):
            if i == len(areas)-1:
                new3Point = [point, areas[0], areas[i]]
            else:
                new3Point = [point, areas[i], areas[i+1]]
            #print(areaThreeAngle(new3Point))
            checkSum += areaThreeAngle(new3Point)
            i += 1
        
        factArea = areaXAngle(areas)
        #print(point)
        #print(areas)
        #print(checkSum)
        #print(factArea)
        if checkSum <= factArea:
            return False
        else:
            return True
        
    def checkWarning(self, points):
        return self.crossMultiPointCheck(points, self.warning)

    def checkDanger(self, points):
        return self.crossMultiPointCheck(points, self.danger)
        
    def crossMultiPointCheck(self, points, areas):
        for point in points:
            if self.crossCheking(point, areas) == False:
                return False
        return True 
        
def areaThreeAngle(coordinates):
    if len(coordinates) != 3:
        return -1
    cs = coordinates
    x1 = cs[0][0]
    y1 = cs[0][1]
    x2 = cs[1][0]
    y2 = cs[1][1]
    x3 = cs[2][0]
    y3 = cs[2][1]
    return abs((x1 * (y2 - y3) + x2 * (y3 - y1)
                + x3 * (y1 - y2)) / 2.0)

               
def areaXAngle(coordinates):
    cs = coordinates
    if len(cs) == 3:
        return areaThreeAngle(cs)
    if len(cs) < 3:
        return -1
    
    x1 = cs[0][0]
    y1 = cs[0][1]
    x2 = cs[len(cs)-1][0]
    y2 = cs[len(cs)-1][1]
    x3 = cs[len(cs)-2][0]
    y3 = cs[len(cs)-2][1]
    last3Angle = [[x1, y1], [x2, y2], [x3, y3]]
    
    return areaThreeAngle(last3Angle) + areaXAngle(cs[:-1])
    