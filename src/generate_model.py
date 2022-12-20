import sys
from pathlib import Path

class GLPK:

	def __init__(self, argv):
		self.file = argv[1]
		self.p = argv[2]
		self.capacity = 0
		self.obj = [] # nombre object , t , i
		self.weight = []  # w
		self.itemMul = [] # n
		self.itemMaxBin = [] # d
		self.maxBin = 0
		self.allContrainte = []
		self.incompatibilites = {}
		self.x = {}
		self.y = {}
		self.z = {} # séparation max des produit par boite
		self.endObj = ""

	def getTextFile(self):
		liste = []
		with open(self.file) as f:
			array = []
			for line in f:  # read rest of lines
				liste.append([int(x) for x in line.split()])
		return liste

	def start(self):
		count = 0
		l = self.getTextFile()
		for i in l[0]:
			self.obj.append(i)
		for i in l[1] : 
			self.capacity = i   
		for i in range(2, 2 + self.obj[1]):
			self.weight.append(l[i][0])
			self.itemMul.append(l[i][1])
			self.itemMaxBin.append(l[i][2])
		for i in range(2+self.obj[1], 2+self.obj[1]+self.obj[2]):
			self.incompatibilites[count] = l[i]
			count += 1
		if(self.p == "0") : 
			self.maxBin = self.heuristic()
		if(self.p == "1" or self.p == "2") :
			if not self.check_valid():
				self.maxBin = self.maximum_Bin_secondary()
			else :
				self.maxBin = self.heuristic_v2()



	#######################################
	# VARIABLES #	
	"""
	Crée les différentes variables
	X , Y et Z
	"""
	def genereBinaryX(self):
		start = 0
		for k in range(self.obj[1]):  # k enumére les différents types
			for j in range(self.maxBin):
				self.x[(k, j)] = "x_"+str(start)
				start += 1

	def genereBinaryY(self):
		start = 0
		for j in range(self.maxBin):
			self.y[j] = "y_"+str(start)
			start+=1

	def genereBinaryZ(self):
		start = 0
		for k in range(self.obj[1]):  # k enumére les différents types
			for j in range(self.maxBin):
				self.z[(k, j)] = "z_"+str(start)
				start += 1

	#######################################
	# HEURISTIC #	
	"""
	Heuristic pour le nombre max de bin p1 et pour le cas des
	incompatibilités p2
	"""
	def maximum_Bin_secondary(self):
		res = 0
		for elem in range(len(self.itemMul)):
			save = 0
			res+=1
			for i in range(self.itemMul[elem]) :
				save += self.weight[elem]
				if save > self.capacity :
					res += 1
					save = self.weight[elem]
				elif save == self.capacity and i<self.itemMul[elem]-1:
					res += 1
					save = 0
		return res
	"""
	Heuristic pour le cas de base p0
	"""
	def heuristic(self) :
		x=[] 
		for i in range(len(self.weight)) : 
			for j in range(self.itemMul[i]) : 
				x.append(self.weight[i])
		n = len(x)
		res = 0
		bin_em = [0]*n
		for i in range(n) : 
			j = 0
			while(j < res) : 
				if(bin_em[j] >= x[i]) : 
					bin_em[j] = bin_em[j] - x[i]
					break
				j+=1
				
			if(j == res) : 
				bin_em[res] = self.capacity - x[i]
				res = res+1
		return res 
	"""
	Heuristic pour le cas des incompatibilités 
	"""
	def heuristic_v2(self) :
		x=[] 
		for i in range(len(self.weight)) : 
			for j in range(self.itemMul[i]) : 
				x.append(self.weight[i])
		n = len(x)
		res = 0
		bin_em = [0]*n
		historique = [[]]*n
		for i in range(n) : 
			j = 0
			while(j < res) : 
				if(bin_em[j] >= x[i] and not self.compare(self.incompatibles(x[i]),historique[j]) ) : 
					bin_em[j] = bin_em[j] - x[i]
					historique[j].append(x[i])
					break
				j+=1
				
			if(j == res) : 
				bin_em[res] = self.capacity - x[i]
				res = res+1
		return res 

	"""
	Compare les différents cas des produits incompatible  
	"""	
	def incompatibles(self,item_type):
		sol = []
		add = False
		for key in self.incompatibilites.keys():
			temp = []
			for elem in self.incompatibilites[key] :
				if elem == item_type :
					add = True
				else :
					temp.append(elem)
			if add :
				sol+=temp
		return sol

	def compare(self,L1,L2):
		for i in L1:
			if i in L2:
				return True
		return False

	"""
	Permet de vérifier si le cas est faisable
	"""
	def check_valid(self):
		for i in range(len(self.itemMul)):
			if self.itemMul[i] > self.itemMaxBin[i] :
				return False
		return True	

	#######################################
	# CONTRAINTE #	

	"""
	contrainte cas de base
	"""
	def contrainte_distribution(self):
		result = []
		for j in range(self.maxBin) :
			temp=""
			for i in range(len(self.weight)) :
				temp+= str(self.weight[i]) + " " + self.x[i,j]
				if i != len(self.weight)-1:
					temp+="+"
			temp +=  "-" + str(self.capacity) + " " +self.y[j] + "<= 0"
			result.append(temp)
		return result

	"""
	contrainte cas de base
	"""
	def contrainte_total_produits(self):
		result=[]
		for i in range(len(self.weight)) :
			temp=""
			for j in range(self.maxBin) :
				temp += self.x[i,j]
				if j != self.maxBin-1:
					temp+="+"
			temp += "="+str(self.itemMul[i])
			result.append(temp)
		return result

	"""
	contrainte cas p1 et p2
	"""
	def contrainte_nbr_max(self): # contrainte nbr max séparation boite
		result = []
		for k in range(self.obj[1]):  # contrainte nbr max
			if self.itemMul[k] > self.itemMaxBin[k]:
				temp = ""
				for j in range(self.maxBin-1) :
					temp+= self.z[k,j] +  "+"
				temp += self.z[k,self.maxBin-1] + "<=" + str(self.itemMaxBin[k])
				result.append(temp)
		return result
	"""
	contrainte cas p1 et p2
	"""
	def contrainte_incompatibilite(self):
		result = []
		for key in self.incompatibilites.keys():
			for j in  range(self.maxBin):
				temp = ""
				for elem in range(len(self.incompatibilites[key])) :
					temp += self.z[elem,j]
					if elem != len(self.incompatibilites[key])-1:
						temp+="+"
				temp += "<= 1"
				result.append(temp)
		return result
	"""
	contrainte cas p1 et p2
	"""
	def contrainte_link_xz(self):
		result = []
		for i in range(len(self.weight)):  # Suite contrainte nbr max
			for j in range(self.maxBin) :
				temp = self.x[i, j] + "-" +str(self.itemMul[i])+ " " +self.z[i, j] + "<= 0"
				result.append(temp)
		return result


	"""
	Minimise tout les bin , fonction de résolution
	"""
	def minimizeObj(self):
		for j in range(self.maxBin-1) :
			self.endObj += self.y[j] + "+"
		self.endObj += self.y[self.maxBin-1]



	def main(self):
		self.start()
		self.genereBinaryX()
		self.genereBinaryY()
		self.genereBinaryZ()
		
		if(self.p == "0" or self.p == "1" or self.p == "2") : 

			self.allContrainte.append(self.contrainte_total_produits())
			self.allContrainte.append(self.contrainte_distribution())   

		if(self.p =="1") :
			self.allContrainte.append(self.contrainte_nbr_max())
			self.allContrainte.append(self.contrainte_link_xz())

		if(self.p =="2") :
			self.allContrainte.append(self.contrainte_total_produits())
			self.allContrainte.append(self.contrainte_distribution())   
			self.allContrainte.append(self.contrainte_nbr_max())
			self.allContrainte.append(self.contrainte_link_xz())


		self.minimizeObj()

		# recupere le nom du fichier et on rajoute le cas
		terp = str(Path(self.file).stem)
		terp = terp.replace("instance", "model")
		terp+="_"+str(self.p)
		terp+=".lp"
		


		# permet d'écrire le modèle en lp
		txt = open(terp, "w")
		txt.write(("Minimize\n"))
		txt.write("\t obj: " + self.endObj + "\n")
		txt.write("Subject To\n")
		count = 0
		for c in self.allContrainte :
			countbis = 0
			for i in range(len(c)) :
				txt.write("\t c_obj_"+ str(count)+"_"+ str(countbis) +  ": " + c[i] + "\n")
				countbis+=1
			count += 1


		txt.write("Bounds\n")

		for key in self.x.keys() :
			txt.write("\t" +self.x[key] +" >= 0"+ "\n")

		txt.write("Integer\n")

		for key in self.x.keys() :
			txt.write("\t" + self.x[key] + "\n")

		txt.write("Binary\n")

		for key in self.y.keys() :
			txt.write("\t" + self.y[key] + "\n")
		for key in self.z.keys():
			txt.write("\t" + self.z[key] + "\n")

		txt.write("End")

		txt.close()





if __name__ == '__main__':
	GLPK(sys.argv).main()