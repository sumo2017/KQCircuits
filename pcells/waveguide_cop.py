import pya
import math
from kqcircuit.pcells.kqcircuit_pcell import KQCirvuitPCell

def up_mod(a, per):
  # Finds remainder in the same direction as periodicity
  if (a*per>0):
    return a % per
  else:
    return a-per*math.floor(a/per)    
    
def arc(R, start, stop, n):
  pts = []
  last = start
  
  alpha_rel = up_mod(stop-start, math.pi * 2) # from 0 to 2 pi
  alpha_step = 2*math.pi/n*(-1 if alpha_rel > math.pi else 1) # shorter dir  n_steps = math.floor((2*math.pi-alpha_rel)/abs(alpha_step) if alpha_rel > math.pi else alpha_rel/abs(alpha_step))
  n_steps = math.floor((2*math.pi-alpha_rel)/abs(alpha_step) if alpha_rel > math.pi else alpha_rel/abs(alpha_step))
  
  alpha = start
    
  for i in range(0,n_steps+1):
    pts.append(pya.DPoint(R * math.cos(alpha), R * math.sin(alpha)))    
    alpha += alpha_step
    last = alpha
  
  if last != stop:
    alpha = stop
    pts.append(pya.DPoint(R * math.cos(alpha), R * math.sin(alpha)))
  
  return pts
     
class WaveguideCopStreight(KQCirvuitPCell):
  """
  The PCell declaration of a streight segment of a transmission line
  """

  def __init__(self):
    super().__init__()
    self.param("l", self.TypeDouble, "Length", default = math.pi)
    self.margin = 5
    
  def display_text_impl(self):
    # Provide a descriptive text for the cell
    return "WaveguideCopStreight(a=" + ('%.1f' % self.a) + ",b=" + ('%.1f' % self.b) + ")"

  def coerce_parameters_impl(self):
    None

  def can_create_from_shape_impl(self):
    return False
  
  def parameters_from_shape_impl(self):
    None
          
  def produce_impl(self):
    # Refpoint in the first end   
    # Left gap
    pts = [
      pya.DPoint(0, self.a/2+0),
      pya.DPoint(self.l, self.a/2+0),
      pya.DPoint(self.l, self.a/2+self.b),
      pya.DPoint(0, self.a/2+self.b)
    ]
    shape = pya.DPolygon(pts)    
    self.cell.shapes(self.layout.layer(self.lo)).insert(shape)        
    # Right gap    
    pts = [
      pya.DPoint(0, -self.a/2+0),
      pya.DPoint(self.l, -self.a/2+0),
      pya.DPoint(self.l, -self.a/2-self.b),
      pya.DPoint(0, -self.a/2-self.b)
    ]
    shape = pya.DPolygon(pts)  
    self.cell.shapes(self.layout.layer(self.lo)).insert(shape)   
    # Protection layer
    w = self.a/2 + self.b + self.margin
    pts = [
      pya.DPoint(0, -w),
      pya.DPoint(self.l, -w),
      pya.DPoint(self.l, w),
      pya.DPoint(0, w)
    ]
    shape = pya.DPolygon(pts)  
    self.cell.shapes(self.layout.layer(self.lp)).insert(shape)   

class WaveguideCopCurve(KQCirvuitPCell):
  """
  The PCell declaration of a curved segment of a transmission line
  
  Cordinate origin is left at the center of the arch.
  """

  def __init__(self):
    super().__init__()
    self.param("alpha", self.TypeDouble, "Curve angle", default = math.pi)
    self.margin = 5
   
  def display_text_impl(self):
    # Provide a descriptive text for the cell
    return "WaveguideCopCurve(a=" + ('%.1f' % self.a) + ",b=" + ('%.1f' % self.b) + ")"

  def coerce_parameters_impl(self):
    None

  def can_create_from_shape_impl(self):
    return False
  
  def parameters_from_shape_impl(self):
    None
          
  def produce_impl(self):
    # Refpoint in the center of the turn
    alphastart = 0
    alphastop = self.alpha
    
    # Left gap
    pts = []  
    R = self.ru-self.a/2
    pts += arc(R,alphastart,alphastop,self.n)
    R = self.ru-self.a/2-self.b
    pts += arc(R,alphastop,alphastart,self.n)     
    shape = pya.DPolygon(pts)
    self.cell.shapes(self.layout.layer(self.lo)).insert(shape)        
    # Right gap
    pts = []  
    R = self.ru+self.a/2
    pts += arc(R,alphastart,alphastop,self.n)
    R = self.ru+self.a/2+self.b
    pts += arc(R,alphastop,alphastart,self.n)
    shape = pya.DPolygon(pts)
    self.cell.shapes(self.layout.layer(self.lo)).insert(shape)   
    # Protection layer
    pts = []  
    R = self.ru-self.a/2-self.b-self.margin
    pts += arc(R,alphastart,alphastop,self.n)
    R = self.ru+self.a/2+self.b+self.margin
    pts += arc(R,alphastop,alphastart,self.n)     
    shape = pya.DPolygon(pts)
    self.cell.shapes(self.layout.layer(self.lp)).insert(shape)        
    
class WaveguideCop(KQCirvuitPCell):
  """
  The PCell declaration for an arbitrary waveguide
  """

  def __init__(self):
    super().__init__()
    self.param("path", self.TypeShape, "TLine", default = pya.DPath([pya.DPoint(0,0),pya.DPoint(1,0)],1))

  def display_text_impl(self):
    # Provide a descriptive text for the cell
    return "Waveguide(a=" + ('%.1f' % self.a) + ",b=" + ('%.1f' % self.b) + ")"
  
  def coerce_parameters_impl(self):
    None

  def can_create_from_shape_impl(self):
    return self.shape.is_path()
  
  def parameters_from_shape_impl(self):
    points = [pya.DPoint(point*self.layout.dbu) for point in self.shape.each_point()]
    self.path = pya.DPath(points, 1)
    
  def transformation_from_shape_impl(self):
    return pya.Trans()
    
  
  def produce_impl(self):      
    points = [point for point in self.path.each_point()]
    
    # For each segment except the last
    segment_last = points[0]
    for i in range(0, len(points)-2):
      # Corner coordinates
      v1 = points[i+1]-points[i]
      v2 = points[i+2]-points[i+1]
      crossing = points[i+1]
      alpha1 = math.atan2(v1.y,v1.x)
      alpha2 = math.atan2(v2.y,v2.x)
      alphacorner = (((math.pi-(alpha2 - alpha1))/2)+alpha2)
      distcorner = v1.vprod_sign(v2)*self.ru / math.sin((math.pi-(alpha2-alpha1))/2)
      corner = crossing + pya.DVector(math.cos(alphacorner)*distcorner, math.sin(alphacorner)*distcorner)
      self.cell.shapes(self.layout.layer(self.la)).insert(pya.DText("%f, %f, %f" % (alpha2-alpha1,distcorner,v1.vprod_sign(v2)),corner.x,corner.y))  
            
      # Streight segment before the corner
      segment_start = segment_last
      segment_end = points[i+1]
      cut = v1.vprod_sign(v2)*self.ru / math.tan((math.pi-(alpha2-alpha1))/2)
      l = segment_start.distance(segment_end)-cut
      angle = 180/math.pi*math.atan2(segment_end.y-segment_start.y, segment_end.x-segment_start.x)
      subcell = self.layout.create_cell("Waveguide streight", "KQCircuit", {
        "a": self.a,
        "b": self.b,
        "l": l # TODO: Finish the list
      })
      transf = pya.DCplxTrans(1,angle,False,pya.DVector(segment_start))
      print("segment",subcell,type(corner),type(transf))
      self.cell.insert(pya.DCellInstArray(subcell.cell_index(),transf))
      segment_last = points[i+1]+v2*(1/v2.abs())*cut
      
      # Curve at the corner
      subcell = self.layout.create_cell("Waveguide curved", "KQCircuit", {
        "a": self.a,
        "b": self.b,
        "alpha": alpha2-alpha1, # TODO: Finish the list,
        "n": self.n,
        "ru": self.ru
      })
      transf = pya.DCplxTrans(1, alpha1/math.pi*180.0-v1.vprod_sign(v2)*90, False, corner)
      print("curve",subcell,type(corner),type(transf))
      self.cell.insert(pya.DCellInstArray(subcell.cell_index(), transf))
    
    # Last segement
    segment_start = segment_last
    segment_end = points[-1]
    l = segment_start.distance(segment_end)
    angle = 180/math.pi*math.atan2(segment_end.y-segment_start.y, segment_end.x-segment_start.x)
    print("Reloaded 2")
    subcell = self.layout.create_cell("Waveguide streight", "KQCircuit", {
      "a": self.a,
      "b": self.b,
      "l": l # TODO: Finish the list
    })
    transf = pya.DCplxTrans(1,angle,False,pya.DVector(segment_start))    
    print("DCell",subcell.cell_index(),transf)
    self.cell.insert(pya.DCellInstArray(subcell.cell_index(),transf)) 
     