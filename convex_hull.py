#!/usr/bin/python3
# why the shebang here, when it's imported?  Can't really be used stand alone, right?  And fermat.py didn't have one...
# this is 4-5 seconds slower on 1000000 points than Ryan's desktop...  Why?


from which_pyqt import PYQT_VER
if PYQT_VER == 'PYQT5':
	from PyQt5.QtCore import QLineF, QPointF, QThread, pyqtSignal
elif PYQT_VER == 'PYQT4':
	from PyQt4.QtCore import QLineF, QPointF, QThread, pyqtSignal
else:
	raise Exception('Unsupported Version of PyQt: {}'.format(PYQT_VER))



import time
import math

#Custom tan class which holds indexes of points, not the points themselves
class Tan:
	def __init__(self, indexL, indexR, slope):
		self.indexL = indexL
		self.indexR = indexR
		self.slope = slope


class ConvexHullSolverThread(QThread):
	def __init__( self, unsorted_points,demo):
		self.points = unsorted_points
		self.pause = demo
		QThread.__init__(self)

	def __del__(self):
		self.wait()

	show_hull = pyqtSignal(list,tuple)
	display_text = pyqtSignal(str)

# some additional thread signals you can implement and use for debugging, if you like
	show_tangent = pyqtSignal(list,tuple)
	erase_hull = pyqtSignal(list)
	erase_tangent = pyqtSignal(list)

#Begin My functions
	#Show hull
	def showHull(self, points):
		lines = []
		for i in range(len(points) - 1):
			lines.append(QLineF(points[i],points[i+1]))
		lines.append(QLineF(points[len(points)-1], points[0]))
		assert( type(lines) == list and type(lines[0]) == QLineF )
		self.show_hull.emit(lines,(255,0,0))

	#Show Tangent
	def showTan(self, p1, p2):
		lines = [QLineF(p1,p2)]
		assert( type(lines) == list and type(lines[0]) == QLineF )
		self.show_tangent.emit(lines,(0,255,0))

	#Erase Tangent
	def eraseTan(self, p1, p2):
		lines = [QLineF(p1,p2)]
		assert( type(lines) == list and type(lines[0]) == QLineF )
		self.erase_tangent.emit(lines)

	#Erase Hull
	def eraseHull(self, points):
		lines = []

		for i in range(len(points) - 1):
			lines.append(QLineF(points[i],points[i+1]))
		lines.append(QLineF(points[len(points)-1], points[0]))
		assert( type(lines) == list and type(lines[0]) == QLineF )
		self.erase_hull.emit(lines)

	#Gets slope of two points
	def slope(self, p1, p2):
		rise = p1.y() - p2.y()
		run = p1.x() - p2.x()
		return rise/run

	#Returns the hull and the index of right most point
	def clockwiseOrder(self, points):
		if len(points) == 1:
			return points, 0
		elif len(points) == 2:
			return points, 1
		else:
			clockwisePoints = [points[0]]
			slopeTo1 = self.slope(points[0], points[1])
			slopeTo2 = self.slope(points[0], points[2])

			#In the rare case the slopes are the same we see which point is closer x-wise
			if slopeTo1 == slopeTo2:
				if points[1].x() < points[2].x():
					clockwisePoints.append(points[1])
					clockwisePoints.append(points[2])
					return clockwisePoints, 2
				else:
					clockwisePoints.append(points[2])
					clockwisePoints.append(points[1])
					return clockwisePoints, 1

			#If the slopes aren't equal, the point with the highest slope is next in clockwise ordering
			if slopeTo1 > slopeTo2:
				clockwisePoints.append(points[1])
				clockwisePoints.append(points[2])
			else:
				clockwisePoints.append(points[2])
				clockwisePoints.append(points[1])
			#Which of those points is right most?
			if clockwisePoints[1].x() > clockwisePoints[2].x():
				return clockwisePoints, 1
			return clockwisePoints,2


	def combine(self, left, rmiL, right, rmiR):
		#This is the upper tan to start with, right most point of left hull and leftmost point of right hull
		#I'm using indexes to keep track of points in order to go counter clockwise or clockwise
		upperTan = Tan(rmiL, 0, self.slope(left[rmiL], right[0]))
		self.showTan(left[upperTan.indexL],right[upperTan.indexR])
		moved1 = True
		moved2 = True
		while moved1 or moved2:
			if self.slope(left[(upperTan.indexL - 1) % len(left)],right[upperTan.indexR]) < upperTan.slope:
				self.eraseTan(left[upperTan.indexL],right[upperTan.indexR])
				upperTan.indexL = (upperTan.indexL - 1) % len(left)
				upperTan.slope = self.slope(left[upperTan.indexL],right[upperTan.indexR])
				self.showTan(left[upperTan.indexL],right[upperTan.indexR])
				moved1 = True
			else:
				moved1 = False

			if self.slope(left[upperTan.indexL],right[(upperTan.indexR+1) % len(right)]) > upperTan.slope:
				self.eraseTan(left[upperTan.indexL],right[upperTan.indexR])
				upperTan.indexR	= ((upperTan.indexR + 1) % len(right))
				upperTan.slope = self.slope(left[upperTan.indexL],right[upperTan.indexR])
				self.showTan(left[upperTan.indexL],right[upperTan.indexR])
				moved2 = True
			else:
				moved2 = False

		#Compute the lower tangent
		lowerTan = Tan(rmiL, 0, self.slope(left[rmiL], right[0]))
		self.showTan(left[lowerTan.indexL],right[lowerTan.indexR])
		moved1 = True
		moved2 = True

		while moved1 or moved2:
			if self.slope(left[(lowerTan.indexL+1) % len(left)],right[lowerTan.indexR]) > lowerTan.slope:
				self.eraseTan(left[lowerTan.indexL],right[lowerTan.indexR])
				lowerTan.indexL = (lowerTan.indexL+1) % len(left)
				lowerTan.slope = self.slope(left[lowerTan.indexL], right[lowerTan.indexR])
				self.showTan(left[lowerTan.indexL],right[lowerTan.indexR])
				moved1 = True
			else:
				moved1 = False

			if self.slope(left[lowerTan.indexL], right[(lowerTan.indexR-1) % len(right)]) < lowerTan.slope:
				self.eraseTan(left[lowerTan.indexL],right[lowerTan.indexR])
				lowerTan.indexR = (lowerTan.indexR-1) % len(right)
				lowerTan.slope = self.slope(left[lowerTan.indexL], right[lowerTan.indexR])
				self.showTan(left[lowerTan.indexL],right[lowerTan.indexR])
				moved2 = True
			else:
				moved2 = False

		#combine hulls
		newHull = []
		newHull.extend(left[0:upperTan.indexL+1]) #gets leftmost of left to first point of uppertan
		if lowerTan.indexR <= upperTan.indexR:
			newHull.extend(right[upperTan.indexR:])
			newHull.extend(right[0:(lowerTan.indexR+1) % len(right)])
		else:
			newHull.extend(right[upperTan.indexR:lowerTan.indexR + 1])
		if lowerTan.indexL != 0:
			newHull.extend(left[lowerTan.indexL:])


		#find new right most index
		newRmi = 0
		for i in range(len(newHull)):
			if newHull[i].x() > newHull[newRmi].x():
				newRmi = i

		#erase tans
		self.eraseTan(left[upperTan.indexL], right[upperTan.indexR])
		self.eraseTan(left[lowerTan.indexL], right[lowerTan.indexR])

		#erase hulls
		self.eraseHull(left)
		self.eraseHull(right)

		return newHull, newRmi






	def getHull(self, points):
		if len(points) < 4:
			return self.clockwiseOrder(points)
		left, rmiL = self.getHull(points[0:math.ceil(len(points)/2)])
		self.showHull(left)
		right, rmiR = self.getHull(points[math.ceil(len(points)/2):])
		self.showHull(right)
		return self.combine(left, rmiL, right, rmiR)

#End my functions

	def run(self):
		assert( type(self.points) == list and type(self.points[0]) == QPointF )

		n = len(self.points)
		print( 'Computing Hull for set of {} points'.format(n) )

		#Sorts points by increasing X value
		t1 = time.time()
		self.points.sort(key=lambda point: point.x(), reverse=False)

		t2 = time.time()
		print('Time Elapsed (Sorting): {:3.3f} sec'.format(t2-t1))

		#Time to compute the hull using divide and conquer
		t3 = time.time()
		answer,rmi = self.getHull(self.points)


		t4 = time.time()

		USE_DUMMY = False
		if USE_DUMMY:
			# this is a dummy polygon of the first 3 unsorted points
			polygon = [QLineF(self.points[i],self.points[(i+1)%3]) for i in range(3)]

			# when passing lines to the display, pass a list of QLineF objects.  Each QLineF
			# object can be created with two QPointF objects corresponding to the endpoints
			assert( type(polygon) == list and type(polygon[0]) == QLineF )
			# send a signal to the GUI thread with the hull and its color
			#self.show_hull.emit(polygon,(255,0,0))

		else:
			self.showHull(answer)

		# send a signal to the GUI thread with the time used to compute the hull
		self.display_text.emit('Time Elapsed (Convex Hull): {:3.3f} sec'.format(t4-t3))
		print('Time Elapsed (Convex Hull): {:3.3f} sec'.format(t4-t3))
