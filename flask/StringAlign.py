import re
import numpy as np
from itertools import combinations, product, chain
from typing import List, Tuple, Any
from collections import namedtuple, deque, defaultdict
from disjointSet import disjoint_set
from copy import deepcopy
from PorterStemmer import PorterStemmer

stemmer = PorterStemmer()

AnchorType = np.ndarray
ScoreType = Any #float, int, etc. #Ord Scoretypr #C++ concept: LessThanComparable

class Param():
	__slots__ = ('_init_value', '_base_point', '_merge_point', '_base_confidence', '_score_map', '_use_stem', '_lowercast')
	def __init__(self, *, init_value = None, base_point = None, merge_point = None, base_confidence = 1, score_map = None, use_stem = False, lowercast = False):
		self._init_value = init_value
		self._base_point = base_point
		self._merge_point = merge_point
		self._base_confidence = base_confidence
		self._score_map = score_map
		self._use_stem = use_stem
		self._lowercast = lowercast
	@property
	def init_value(self):
		return self._init_value
	@init_value.setter
	def init_value(self, n):
		self._init_value = n
	@property
	def base_point(self):
		return self._base_point
	@base_point.setter
	def base_point(self, f):
		#f :: List[str] -> List[str] -> float
		self._base_point = f
	@property
	def merge_point(self):
		return self._merge_point
	@merge_point.setter
	def merge_point(self, f):
		#f :: (List[str], List[str]) -> (List[str], List[str]) -> (float, List[anchor]) -> (float, List[anchor]) -> float
		self._merge_point = f
	@property
	def base_confidence(self):
		return self._base_confidence
	@base_confidence.setter
	def base_confidence(self, n):
		self._base_confidence = n
	@property
	def score_map(self):
		return self._score_map if self._score_map is not None else lambda c, state: {i: j.similarity for i, j in state.Dict.items()}
	@score_map.setter
	def score_map(self, f):
		#f :: List[float] -> State[int, Dict[(int, int): Ans(float, List[anchor])]] -> Dict[(int, int): float]
		self._score_map = f
	@property
	def use_stem(self):
		return self._use_stem
	@use_stem.setter
	def use_stem(self, n):
		self._use_stem = n
	@property
	def lowercast(self):
		return self._lowercast
	@lowercast.setter
	def lowercast(self, n):
		self._lowercast = n

class StringAlign():
	c1, c2, c3 = re.compile(R"([^\w\s'])"), re.compile(R"\s+"), re.compile(R"^\s|\s$")
	graph_module = None
	graph_module_tryorder = ['networkx', 'pyswip']
	init_similarity = 0
	State = namedtuple("State", "length Dict")
	Ans = namedtuple('Ans', "similarity anchors")
	join = staticmethod(lambda l: " ".join(l))
	def __init__(self, *args):
		self._state = None
		self._big_anchor_state = None
		self._l = []
		self.push(*args)
	def push(self, *args):
		l = []
		for i in args:
			if type(i) is str:
				l.append(i)
			else:
				l.extend(i)
		l = [self.c3.sub("", self.c2.sub(" ", self.c1.sub(R" \1 ", s))).split() for s in l]
		self._l.extend(l)
	def push_list(self, l):
		self.push(l)
	def concat(self, n):
		self._l.extend(n._l)
	def __iadd__(self, n):
		if type(n) is not type(self):
			self.push_list(n)
		else:
			self.concat(n)
		return self
	def __add__(self, n):
		sol = self.copy() #create a copy
		sol.__iadd__(n)
		return sol
	def __radd__(self, n):
		return self.__add__(n)
	def __str__(self):
		state, l, join = self._state, self._l, self.join
		if state is None:
			return "No state is ready."
		n = state.length
		s = ""
		for i, j in combinations(range(n), 2):
			ans = state.Dict[(i, j)]
			s += f"string {(i, j)}\n{join(l[i])}\n{join(l[j])}\nhas similarity {ans.similarity}\nfix points are: {[tuple(i) for i in ans.anchors]}\n\n"
		return s[:-2]
	@property
	def sentences(self): #equivalent to self[:]
		return self[:]
	def __getitem__(self, val):
		if isinstance(val, slice):
			return [self.__class__.join(i) for i in self._l[val]]
		return self.__class__.join(self._l[val])
	def copy(self):
		"""
		create a copy of object
		the content of each list in _l is not allowed to be changed
		, so it's no problem for shallow copy
		"""
		sol = type(self)()
		sol._l = self._l.copy() #
		return sol
	@classmethod
	def decide_graph_module(cls):
		if cls.graph_module is not None:
			return
		for module in cls.graph_module_tryorder:
			try:
				exec(f'import {module}')
			except ImportError: #precisely, ModuleNotFoundError in Py3.6
				continue
			else:
				cls.graph_module = module
				return
		print('No module in {} has been installed!'.format(', '.join(cls.graph_module_tryorder)))
	def evaluate(self, param: Param):
		""" return state after comparing strings """
		l = self._l
		n = len(l)
		state = self.__class__.State(n, dict())
		if param.use_stem:
			l = [[stemmer.stem(word, 0, len(word) - 1) for word in s] for s in l]
		if param.lowercast:
			l = [[word.lower() for word in s] for s in l]
		for i, j in combinations(range(n), 2):
			get = self.__class__.compare(l[i], l[j], param)
			#get = get[0], list(get[1])
			state.Dict[(i, j)] = get
		self._state = state
	def big_anchor_concat_heuristic(self, param: Param, confidence: list = None):
		""" provisional big-anchor function """

		if self._state is None: #exception-like condition, maybe NoStateException
			print('No state is ready!')
			return
		state, n = self._state, self._state.length
		if confidence is None or len(confidence) != n: 
			confidence = [param.base_confidence] * n
		scores = param.score_map(confidence, state)
		sentences_set = disjoint_set.from_iterable(range(n)) # a disjoint set of sentences
		word_set = disjoint_set.from_iterable(chain.from_iterable([(i, j) for j in range(len(self._l[i]))] for i in range(n))) # a disjoint set of words in sentences
		pairs = sorted(state.Dict.keys(), key = (lambda k: scores[k]), reverse = True)
		for i, j in pairs:
			if sentences_set.is_same(i, j):
				continue
			anchors = state.Dict[(i, j)].anchors
			for k, l in anchors:
				word_set.union((i, k), (j, l))
			sentences_set.union(i, j)
		self._big_anchor_state = {'word_set': word_set} # words_set put every same word into one set
		return self._big_anchor_state
		#this function should return one that contains word_set
		#sets = list(word_set.sets())
		#all the sentences should become same
	def big_anchor_concat_james(self, param: Param, *args, **kwargs):
		if self._state is None: #exception-like condition, maybe NoStateException
			print('No state is ready!')
			return
		state = self._state
		assert state.length == 4, "should be 4 sentences."
		comb = sorted(state.Dict.keys(), key = (lambda i: state.Dict[i].similarity), reverse = True)
		best_comb = comb[0]
		another_comb = tuple(i for i in range(4) if i not in best_comb)
		mapping = {j: i for i, j in enumerate([*best_comb, *another_comb])}
		r_mapping = {i: j for i, j in enumerate([*best_comb, *another_comb])}
		sticks = [[{0: i, 1: j} for i, j in state.Dict[best_comb].anchors], [{2: i, 3: j} for i, j in state.Dict[another_comb].anchors]]
		after_change_sticks = [[{0: i, 1: j} for i, j in state.Dict[another_comb].anchors], [{2: i, 3: j} for i, j in state.Dict[best_comb].anchors]]
		#word_set = disjoint_set.from_iterable(chain.from_iterable([(i, j) for j in range(len(self._l[i]))] for i in range(4)))
		l = self._l
		if param.use_stem:
			l = [[stemmer.stem(word, 0, len(word) - 1) for word in s] for s in l]
		elif param.lowercast:
			l = [[word.lower() for word in s] for s in l]
		max_score_top_to_bottom, best_sticks_top_to_bottom = self.__class__._big_anchor_concat_james_helper([l[i] for i in best_comb] + [l[i] for i in another_comb], sticks)
		max_score_bottom_to_top, best_sticks_bottom_to_top = self.__class__._big_anchor_concat_james_helper([l[i] for i in another_comb] + [l[i] for i in best_comb], after_change_sticks)
		best_sticks_bottom_to_top = [[{(k+2)%4: i for k, i in d.items()} for d in best_sticks_bottom_to_top[1]], [{(k+2)%4: i for k, i in d.items()} for d in best_sticks_bottom_to_top[0]]]
		best_sticks = [best_sticks_top_to_bottom[0] , best_sticks_bottom_to_top[1]]
		for i in range(0, len(best_sticks[0])):
			for j in range(0, len(best_sticks[1])):
				if all(elem in best_sticks[1][j].items() for elem in best_sticks[0][i].items()):
					best_sticks[0][i] = {}
				elif all(elem in best_sticks[0][i].items() for elem in best_sticks[1][j].items()):
					best_sticks[1][j] = {}
				elif any(elem in best_sticks[0][i].items() for elem in best_sticks[1][j].items()):
					if len(best_sticks[0][i]) >= len(best_sticks[1][j]):
						best_sticks[1][j] = {}
					else:
						best_sticks[0][i] = {}
		best_sticks[0] = list(filter(lambda a: len(a) > 0, best_sticks[0]))
		best_sticks[1] = list(filter(lambda a: len(a) > 0, best_sticks[1]))

		best_sticks = best_sticks[0] + best_sticks[1] #List[List[Dict]] -> List[Dict]

		crosses = {}
		for i in range(0,len(best_sticks)):
			crosses[i] = []
		for i in range(0, len(best_sticks) - 1):
			for j in range(i+1, len(best_sticks)):
				if len(best_sticks[i]) >= 3 and len(best_sticks[j]) >= 3:
					order = []
					find_cross = False
					for i_word in best_sticks[i].items():
						for j_word in best_sticks[j].items():
							if i_word[0] ==  j_word[0]:
								if len(order) == 0:
									if i_word[1] > j_word[1]:
										order = [j, i]
									else:
										order = [i, j]
								else:
									if i_word[1] > j_word[1] and order[0] == i:
										crosses[i].append(j)
										crosses[j].append(i)
										find_cross = True
										break
									elif i_word[1] < j_word[1] and order[0] == j:
										crosses[i].append(j)
										crosses[j].append(i)
										find_cross = True
										break
						if find_cross == True:
							break
		
		# solve cross sticks
		no_cross_sticks = []
		while any(len(crosses[x]) > 0 for x in crosses):
			max_len = 0
			index_to_delete = -1
			for i in range(0, len(crosses)):
				if len(crosses[i]) > max_len:
					index_to_delete = i
					max_len = len(crosses[i])
			
			if len(best_sticks[index_to_delete]) == 4:
				#no_cross_sticks.append([best_sticks[index_to_delete][0], best_sticks[index_to_delete][1]])
				#no_cross_sticks.append([best_sticks[index_to_delete][2], best_sticks[index_to_delete][3]])
				no_cross_sticks.append({0: best_sticks[index_to_delete][0], 1: best_sticks[index_to_delete][1]})
				no_cross_sticks.append({2: best_sticks[index_to_delete][2], 3: best_sticks[index_to_delete][3]})
				best_sticks[index_to_delete] = {}
			
			elif 0 in best_sticks[index_to_delete].keys() and 1 in best_sticks[index_to_delete].keys():
				no_cross_sticks.append({0: best_sticks[index_to_delete][0], 1: best_sticks[index_to_delete][1]})
				best_sticks[index_to_delete] = {}
			
			elif 2 in best_sticks[index_to_delete].keys() and 3 in best_sticks[index_to_delete].keys():
				no_cross_sticks.append({2: best_sticks[index_to_delete][2], 3: best_sticks[index_to_delete][3]})
				best_sticks[index_to_delete] = {}
			
			crosses[index_to_delete] = {}
			for i in range(0, len(crosses)):
				if index_to_delete in crosses[i]:
					crosses[i].remove(index_to_delete)
			
		best_sticks = list(filter(lambda a: len(a) > 0, best_sticks))
		no_cross_sticks += best_sticks #List[Dict]
		word_set = disjoint_set.from_iterable(chain.from_iterable([(i, j) for j in range(len(l[i]))] for i in range(4)))
		for d in no_cross_sticks:
			if len(d) <= 1:
				continue
			i = iter(d.items())
			s, index = next(i) #consume
			s = r_mapping[s]
			for s_i, index_i in i:
				word_set.union((s, index), (r_mapping[s_i], index_i))
		self._big_anchor_state = {'word_set': word_set}
		return self._big_anchor_state
	@classmethod
	def _big_anchor_concat_james_word_counter(cls, strings, word_to_count):
		count = 0
		for i in range(0, len(strings)):
			for word in strings[i]:
				if word == word_to_count:
					count += 1
		return count
	@classmethod
	def _big_anchor_concat_james_helper(cls, strings, sticks, shifts = [0, 0, 0, 0], shifts_diff = [0, 0, 0, 0], mode = 'right'):
		strings_len = [len(s) for s in strings]
		
		now_score = -np.inf
		max_score = -np.inf
		left_max_score = 0
		right_max_score = 0

		now_sticks = []
		best_sticks = sticks
		left_best_sticks = []
		right_best_sticks = []
		find_stick = False
		
		if mode == "right":
			for i in range(0, 2):
				for j in range(0, len(sticks[i])):
					for k in sticks[i][j].keys():
						sticks[i][j][k] -= shifts_diff[k]
		
		top_stick_index = 0
		for top_stick in sticks[0]:
			string2_index = 0
			for string2_word in strings[2]:
				if string2_word == strings[0][top_stick[0]]:
					find_stick = True
					
					is_stick = False
					left_strings = [strings[0][0:top_stick[0]], strings[1][0:top_stick[1]], strings[2][0:string2_index]]
					right_strings = [strings[0][top_stick[0] + 1:strings_len[0]],
												strings[1][top_stick[1] + 1:strings_len[1]],
												strings[2][string2_index + 1:strings_len[2]]]
					left_sticks = [sticks[0][0:top_stick_index]]
					right_sticks = [sticks[0][top_stick_index + 1:len(sticks[0])]]
					
					bottom_stick_index = 0
					for bottom_stick in sticks[1]:
						if bottom_stick[2] == string2_index:
							is_stick = True
							break
						bottom_stick_index += 1

					#the word is a stick
					if is_stick == True:
						left_strings.append(strings[3][0:sticks[1][bottom_stick_index][3]])
						right_strings.append(strings[3][sticks[1][bottom_stick_index][3] + 1:strings_len[3]])
						left_sticks.append(sticks[1][0:bottom_stick_index])
						if bottom_stick_index + 1 >= 0:
							right_sticks.append(sticks[1][bottom_stick_index + 1:len(sticks[1])])
						else:
							right_sticks.append([])
						
						left_shifts = shifts
						right_shifts = [shifts[0] + 1 + top_stick[0], shifts[1] + 1 + top_stick[1], shifts[2] + 1 + string2_index, shifts[3] + 1 + sticks[1][bottom_stick_index][3]]
						left_shifts_diff = [0, 0, 0, 0]
						right_shifts_diff = []
						for i in range(0, 4):
							right_shifts_diff.append(right_shifts[i] - shifts[i])
						
						left_max_score, left_best_sticks = cls._big_anchor_concat_james_helper(left_strings, left_sticks, left_shifts, left_shifts_diff, "left")
						right_max_score, right_best_sticks = cls._big_anchor_concat_james_helper(right_strings, right_sticks, right_shifts, right_shifts_diff, "right")
						now_score = left_max_score + 4 + right_max_score
						if now_score > max_score:
							adjust_top_stick = {k: i + shifts[k] for k, i in top_stick.items()}
							adjust_bottom_stick = {k: i + shifts[k] for k, i in sticks[1][bottom_stick_index].items()}
							
							max_score = now_score
							best_sticks = [left_best_sticks[0] + [{**adjust_top_stick, **adjust_bottom_stick}] + right_best_sticks[0], left_best_sticks[1] + right_best_sticks[1]]
					
					#the word is not a stick
					elif is_stick == False and strings_len[3] > 0:
						string3_to_count_index_start = 0
						string3_to_count_index_finish = strings_len[3] - 1
						bottom_stick_index_before = -1
						bottom_stick_index_after = -1
						for bottom_stick in sticks[1]:
							if bottom_stick[2] < string2_index:
								string3_to_count_index_start = bottom_stick[3] + 1
								bottom_stick_index_before += 1
							else:
								string3_to_count_index_finish = bottom_stick[3] - 1
								bottom_stick_index_after = bottom_stick_index_before + 1
								break
							
						string3_start_right_index = string3_to_count_index_finish + 1
						for string3_middle_index in range(string3_to_count_index_start, string3_to_count_index_finish + 1):
							if cls._big_anchor_concat_james_word_counter(left_strings, strings[3][string3_middle_index]) < cls._big_anchor_concat_james_word_counter(right_strings, strings[3][string3_middle_index]):
								string3_start_right_index = string3_middle_index
								break
						
						left_strings.append(strings[3][0:string3_start_right_index])
						right_strings.append(strings[3][string3_start_right_index:strings_len[3]])
						left_sticks.append(sticks[1][0:bottom_stick_index_before + 1])
						if bottom_stick_index_after >= 0:
							right_sticks.append(sticks[1][bottom_stick_index_after:len(sticks[1])])
						else:
							right_sticks.append([])
						
						left_shifts = shifts
						right_shifts = [shifts[0] + 1 + top_stick[0], shifts[1] + 1 + top_stick[1], shifts[2] + 1 + string2_index, shifts[3] + 1 + string3_start_right_index-1]
						left_shifts_diff = [0, 0, 0, 0]
						right_shifts_diff = []
						for i in range(0, 4):
							right_shifts_diff.append(right_shifts[i] - shifts[i])
						
						left_max_score, left_best_sticks = cls._big_anchor_concat_james_helper(left_strings, left_sticks, left_shifts, left_shifts_diff, "left")
						right_max_score, right_best_sticks = cls._big_anchor_concat_james_helper(right_strings, right_sticks, right_shifts, right_shifts_diff, "right")
						
						now_score = left_max_score + 3 + right_max_score
						if now_score > max_score:
							adjust_top_stick = {k: i + shifts[k] for k, i in top_stick.items()}
							
							max_score = now_score
							best_sticks = [left_best_sticks[0] + [{**adjust_top_stick, 2: string2_index + shifts[2]}] + right_best_sticks[0], left_best_sticks[1] + right_best_sticks[1]]

				string2_index += 1
			
			string3_index = 0
			for string3_word in strings[3]:
				if string3_word == strings[0][top_stick[0]]:
					find_stick = True
					is_stick = False
					left_strings = [strings[0][0:top_stick[0]], strings[1][0:top_stick[1]], strings[3][0:string3_index]]
					right_strings = [strings[0][top_stick[0] + 1:strings_len[0]],
												strings[1][top_stick[1] + 1:strings_len[1]],
												strings[3][string3_index + 1:strings_len[3]]]
					left_sticks = [sticks[0][0:top_stick_index]]
					right_sticks = [sticks[0][top_stick_index + 1:len(sticks[0])]]
					
					for bottom_stick in sticks[1]:
						if bottom_stick[3] == string3_index:
							is_stick = True
							break
					
					#the word is not a stick
					if is_stick == False and strings_len[2] > 0:
						
						string2_to_count_index_start = 0
						string2_to_count_index_finish = strings_len[2] - 1
						bottom_stick_index_before = -1
						bottom_stick_index_after = -1
						for bottom_stick in sticks[1]:
							if bottom_stick[3] < string3_index:
								string2_to_count_index_start = bottom_stick[2] + 1
								bottom_stick_index_before += 1
							else:
								string3_to_count_index_finish = bottom_stick[2] - 1 #???
								bottom_stick_index_after = bottom_stick_index_before + 1
								break
							
						string2_start_right_index = string2_to_count_index_finish + 1
						for string2_middle_index in range(string2_to_count_index_start, string2_to_count_index_finish + 1):
							if cls._big_anchor_concat_james_word_counter(left_strings, strings[2][string2_middle_index]) < cls._big_anchor_concat_james_word_counter(right_strings, strings[2][string2_middle_index]):
								string2_start_right_index = string2_middle_index
								break
						
						left_strings.insert(2, strings[2][0:string2_start_right_index])
						right_strings.insert(2, strings[2][string2_start_right_index:strings_len[2]])
						left_sticks.insert(2, sticks[1][0:bottom_stick_index_before + 1])
						if bottom_stick_index_after >= 0:
							right_sticks.insert(2, sticks[1][bottom_stick_index_after:len(sticks[1])])
						else:
							right_sticks.insert(2, [])
						
						left_shifts = shifts
						right_shifts = [shifts[0] + 1 + top_stick[0], shifts[1] + 1 + top_stick[1], shifts[2] + 1 + string2_start_right_index-1, shifts[3] + 1 + string3_index]
						left_shifts_diff = [0, 0, 0, 0]
						right_shifts_diff = []
						for i in range(0, 4):
							right_shifts_diff.append(right_shifts[i] - shifts[i])
						
						left_max_score, left_best_sticks = cls._big_anchor_concat_james_helper(left_strings, left_sticks, left_shifts, left_shifts_diff, "left")
						right_max_score, right_best_sticks = cls._big_anchor_concat_james_helper(right_strings, right_sticks, right_shifts, right_shifts_diff, "right")
						
						now_score = left_max_score + 3 + right_max_score
						if now_score > max_score:
							adjust_top_stick = {k: i + shifts[k] for k, i in top_stick.items()}
							max_score = now_score
							best_sticks = [left_best_sticks[0] + [{**adjust_top_stick, 3: string3_index + shifts[3]}] + right_best_sticks[0], left_best_sticks[1] + right_best_sticks[1]]

				string3_index += 1
			
			top_stick_index += 1
		
		#base case
		if find_stick == False:
			top_stick_number = len(sticks[0])
			bottom_stick_number = len(sticks[1])
			max_score = -1*(strings_len[0] + strings_len[1] + strings_len[2] + strings_len[3]) + bottom_stick_number * 2 * 2
		
		if mode == "right":
			for i in range(0,2):
				for j in range(0,len(sticks[i])):
					for k in sticks[i][j].keys():
						sticks[i][j][k] += shifts_diff[k]

		return max_score, best_sticks
	def give_graph(self):
		if self._state is None: #exception-like condition, maybe NoStateException
			print('No state is ready!')
			return
		state, n = self._state, self._state.length
		if self._big_anchor_state is None:
			print('No big anchor state is ready!')
			return
		if 'graph' in self._big_anchor_state:
			return self._big_anchor_state['graph']
		word_set = self._big_anchor_state['word_set']
		self.decide_graph_module()
		if self.graph_module == 'networkx':
			import networkx as nx
			G = nx.DiGraph()
			index = word_set.index()
			origin_word_mapping = defaultdict(list) #adapted for word stemming
			for i in range(n):
				G.add_node(index[(i, 0)])
				origin_word_mapping[index[(i, 0)]].append(self._l[i][0])
				for j, word in enumerate(self._l[i][1:], 1):
					G.add_edge(index[(i, j - 1)], index[(i, j)])
					origin_word_mapping[index[(i, j)]].append(self._l[i][j])
				for j, word in enumerate(self._l[i]):
					if 'appearance' not in G.nodes[index[(i, j)]]:
						G.nodes[index[(i, j)]]['appearance'] = []
					G.nodes[index[(i, j)]]['appearance'].append(i)
			for i, l in origin_word_mapping.items():
				"""
				choose the word to represent
				only 1 mode now: choose the first appearence
				"""
				G.nodes[i]['word'] = l[0]
			self._big_anchor_state['graph'] = G
			return G
		elif self.graph_module == 'pyswip':
			from pyswip import Prolog
			prolog = Prolog()
			prolog.consult('knowledge.pl')
			#clear the previos graph which is created in this object
			deque(prolog.query(f'clear_register({id(self)})'), maxlen = 0)
			index = word_set.index()
			id_word_map = defaultdict(list) #prevent overlapping, adapted for word stemming
			for i in range(n):
				id_word_map[index[(i, 0)]].append(self._l[i][0])
				for j, word in enumerate(self._l[i][1:], 1):
					prolog.assertz(f'edge({index[(i, j - 1)]}, {index[(i, j)]})')
					id_word_map[index[(i, j)]].append(word)
				for j in range(len(self._l[i])):
					prolog.assertz(f'appear({index[(i, j)]}, {i})')
			for word_id, words in id_word_map.items():
				"""
				choose the word to represent
				only 1 mode now: choose the first appearence
				"""
				word = words[0]
				
				prolog.assertz(f"word({word_id}, '{word}')") #word is atom, not string (list of codes)
				prolog.assertz(f'node_register({id(self)}, {word_id})') #register the word ID under a key (python ID of self)
			#prolog.assertz('all_node([{}])'.format(', '.join([str(i) for i in id_word_map.keys()])))
			self._big_anchor_state['graph'] = prolog
			return prolog
		elif self.graph_module is None:
			print('Failed to draw graph!')
			return
	def str_big_anchor(self):
		"""
		function to return string represent the solution
		"""
		G = self.give_graph()
		if G is None:
			print('Fail to print big anchor.')
			return
		n = self._state.length
		if self.graph_module == 'networkx':
			import networkx as nx
			id_list = list(nx.algorithms.dag.topological_sort(G))
			id_len = {i: len(G.nodes[i]['word']) for i in id_list}
			str_list = [[' ' * id_len[i] for i in id_list] for _ in range(n)]
			for i, word_id in enumerate(id_list):
				node = G.nodes[word_id]
				word = node['word']
				for s in node['appearance']:
					str_list[s][i] = word
			return ('\n'.join([' '.join(s) for s in str_list]))
		elif self.graph_module == 'pyswip':
			query = next(G.query(f'all_node({id(self)}, L), topological_sort(L, Sol), grab_word(Sol, Words)'))
			id_list, words = query['Sol'], [str(i) for i in query['Words']] #query['Words'] is a list of Atom object (this is a problem of pyswip), so call str() to make it string.
			id_len = {i: len(word) for i, word in zip(id_list, words)}
			str_list = [[' ' * id_len[i] for i in id_list] for _ in range(n)]
			for i, (word_id, word) in enumerate(zip(id_list, words)):
				for q in G.query(f'appear({word_id}, N)'):
					str_list[q['N']][i] = word
			return ('\n'.join([' '.join(s) for s in str_list]))
	def final_result(self, weight, threshold):
		G = self.give_graph()
		if G is None:
			print('Fail to get final result.')
			return
		if self.graph_module == 'networkx':
			import networkx as nx
			id_list = list(nx.algorithms.dag.topological_sort(G))
			votes = map(lambda word_id: sum(weight[s] for s in G.nodes[word_id]['appearance']), id_list)
			return (G.nodes[word_id]['word'] for vote, word_id in zip(votes, id_list) if vote >= threshold)
		elif self.graph_module == 'pyswip':
			id_list = next(G.query(f'all_node({id(self)}, L), topological_sort(L, Sol)'))['Sol']
			votes = map(lambda word_id: sum(weight[q['N']] for q in G.query(f'appear({word_id}, N)')), id_list)
			return (next(G.query(f'word({word_id}, Word)'))['Word'] for vote, word_id in zip(votes, id_list) if vote >= threshold)
	@classmethod
	def compare(cls, l1: List[str], l2: List[str], param: Param):
		anchors = cls._anchors(l1, l2)
		return cls._compare_detail(l1, l2, param, anchors, {})
	@staticmethod
	def _anchors(l1: List[str], l2: List[str]) -> List[AnchorType]:
		"""
		input two 'string' which is splitted into list of words.
		output all pairs of indexs which means:
			(i, j): l1[i] ==   l2[j]
		And, (i, j) will be a numpy array and that makes mathematical work easier.
		"""
		s = set(l1) & set(l2) # return the same words in two list of words
		sol = []
		for c in s:
			i1, i2 = np.argwhere(np.array(l1) == c).reshape([-1]), np.argwhere(np.array(l2) == c).reshape([-1])
			sol.extend([np.array(i) for i in product(i1, i2)])
		return sol
	@classmethod
	def _compare_split(cls, l1: List[str], l2: List[str], param: Param, anchors: List[AnchorType], memo: dict, now_anchor: AnchorType) -> Tuple[ScoreType, List[AnchorType]]:
		"""
		recursion function that always called by _compare_detail
		deal with the step: considering an anchor being fixed, calculate the max possible point(score) it could be.
		And because that, the splitting step (breaking sentences from the fixed spot) is executed here.
		So there is 'split' in its name.
		base case of recursion is factly done here.
		input:
			l1, l2: two 'string' which is splitted into list of words.
			param: base_point and merge_point is used here.
				base_point: called when no anchor available, input l1, l2, output the score(point)
				merge_point: called to merge the score(point) of left and of right.
							 input (left of now_anchor of l1, of l2), (right of now_anchor of l1, of l2),
									ans returned by left recursion, and that by right one.
							 output the score(point)
							 ans :: return type of _compare_xxx
			anchors
			memo: not used in this function. just pass it into _compare_detail
			now_anchor: meaning which anchor is fixed at the very step.
		output: ans :: Ans(float, List[anchor]), as the highest similarity, anchors, same as _compare_detail
		"""
		if now_anchor is None: # base case 
			return param.base_point(l1, l2), []
		left_child = (l1[:now_anchor[0]], l2[:now_anchor[1]]) # words on the left of the anchor
		right_child = (l1[(now_anchor[0] + 1):], l2[(now_anchor[1] + 1):]) # words on the right of the anchor
		left_anchor = [anchor for anchor in anchors if np.all(anchor < now_anchor)] # lisf of anchors on the left child
		right_anchor = [anchor - now_anchor - 1 for anchor in anchors if np.all(anchor > now_anchor)]  # lisf of anchors on the right child
		left_ans = cls._compare_detail(*left_child, param, left_anchor, memo)
		right_ans = cls._compare_detail(*right_child, param, right_anchor, memo)
		sol_anchor = left_ans.anchors + [now_anchor] + [anchor + now_anchor + 1 for anchor in right_ans.anchors]
		sol_simi = param.merge_point(left_child, right_child, left_ans, right_ans)
		return cls.Ans(sol_simi, sol_anchor)
	@classmethod
	def _compare_detail(cls, l1: List[str], l2: List[str], param: Param, anchors: List[AnchorType], memo: dict) -> Tuple[ScoreType, List[AnchorType]]:
		"""
		recursion function that called from outside (i.e., it is the entry of recursion) or by _compare_split
		deal with the step: given all possible anchors, I want to know which anchor, when fixing it first, can get the highest point(score)
		the step of traversing all anchors is done here.
		the step of comparing all score(point) and choosing the max is also done here.
		base case of recursion is done by calling _compare_split with now_anchor being None
		input:
			l1, l2: two 'string' which is splitted into list of words.
			param: init_value is used here.
				init_value: the starting point(score) meaning the lower bound of scoring algorithm
			anchors
			memo: a dict recording all results of having-appeared situations made of l1, l2, and anchors.
		output: ans :: Ans(float, List[anchor]), as the highest similarity, anchors, same as _compare_split
		"""
		hashable_sign = (tuple(l1), tuple(l2), tuple([tuple(i) for i in anchors]))
		if hashable_sign not in memo:
			similarity, anchors_to_choose = param.init_value, []
			if len(anchors) == 0:
				simi, use_anchors = cls._compare_split(l1, l2, param, anchors, memo, None) # call base case 
				if simi > similarity:
					similarity, anchors_to_choose = simi, use_anchors
			for anchor in anchors: #if executing above, the for-loop will not be executed
				simi, use_anchors = cls._compare_split(l1, l2, param, anchors, memo, np.array(anchor))
				if simi > similarity:
					similarity, anchors_to_choose = simi, use_anchors
			memo[hashable_sign] = cls.Ans(similarity, anchors_to_choose)
		return memo[hashable_sign]

def give_param(way):
	p = Param()
	if way == 'wayne':
		p.init_value = 0.0
		p.base_point = lambda l1, l2: 1 / (len(l1) + len(l2) + 1) # base point is 1 divided by number of words in two lists plus 1 
		def merge_point(left, right, ans1, ans2):
			left_len = len(left[0]) + len(left[1])
			right_len = len(right[0]) + len(right[1])
			left_point, right_point = ans1.similarity, ans2.similarity
			return (left_point * left_len + right_point * right_len + 2) / (left_len + right_len + 2)
		p.merge_point = merge_point
	elif way == 'james':
		p.init_value = -np.inf 
		p.base_point = lambda l1, l2: -(len(l1) + len(l2)) # base point is negative of number of words in two lists
		p.merge_point = lambda l, r, a1, a2: a1.similarity + a2.similarity + 2
	return p

if __name__ == '__main__':
	S = StringAlign()


	S += ['later that day when the princess was sitting at the table something with her coming up the marble stairs',
	'Later that day one that princess was sitting at the table something was heard coming up the marble stairs']
	
	S += ['later that day when the princess was sitting at the table something with her coming up the marble stairs',
	'later that day when the princess was sitting at the table something was heard coming up the marbles dears']

	p = give_param('wayne')
	p.lowercast = True
	p.use_stem = True

	S.evaluate(p)
	print(S)
	#x = S.big_anchor_concat_james(p)
	x = S.big_anchor_concat_heuristic(p)
	x = x['word_set']
	print(S.str_big_anchor())
	print(x)
	#print(x.copy().sets())
	result = S.final_result([1.5, 1, 1, 1], 2)
	#print(list(result))
	#x = S.big_anchor_concat_heuristic(p)
	#print(S.str_big_anchor())
	result = S.final_result([1.5, 1, 1, 1], 3)
	#print(list(result))
