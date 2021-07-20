class _node():
	def __init__(self):
		self.ptr = None
		self.rank = 0
	def concat(self, ptr):
		self.ptr = ptr
	def find_root(self):
		if self.ptr is None:
			return self
		ptr = self.ptr.find_root()
		self.ptr = ptr
		return ptr

class disjoint_set():
	def __init__(self, *args):
		self._dict = dict()
		self.push(*args)
	@classmethod
	def from_iterable(cls, l):
		return cls(*l)
	def push(self, *args):
		for i in args:
			if i in self._dict:
				continue
			self._dict[i] = _node()
	def push_iterable(self, l):
		self.push(*l)
	def find(self, n):
		if n not in self._dict:
			return None
		return self._dict[n].find_root()
	def is_same(self, m, n) -> bool:
		return self.find(m) is self.find(n)
	def union(self, m, n):
		i, j = self.find(m), self.find(n)
		if i is None:
			raise KeyError(f'{repr(m)} is not found!')
		elif j is None:
			raise KeyError(f'{repr(n)} is not found!')
		if i is j:
			return
		if i.rank > j.rank:
			j.concat(i)
		else:
			i.concat(j)
			if i.rank == j.rank:
				j.rank += 1
	def index(self): #many to one
		return {key: id(node.find_root()) for key, node in self._dict.items()}
	def reversed_index(self): #one to many, so using list
		from collections import defaultdict
		index = self.index()
		dic = defaultdict(list)
		for key, i in index.items():
			dic[i].append(key)
		return dic
	def sets(self):
		dic = self.reversed_index()
		return dic.values()
	def __str__(self):
		d = self.sets()
		s = [f"{{{', '.join([str(i) for i in l])}}}" for l in d]
		return f"{{{', '.join(s)}}}"
	def _rebuild_dict(self):
		d = self.sets()
		_dict = dict()
		for l in d:
			if len(l) == 1:
				_dict[l[0]] = _node()
			else:
				n = _node()
				n.rank = 1
				_dict[l[0]] = n
				for k in l[1:]:
					p = _node()
					p.concat(n)
					_dict[k] = p
		return _dict
	def copy(self):
		sol = type(self)()
		sol._dict = self._rebuild_dict()
		return sol
	def rebuild(self):
		self._dict = self._rebuild_dict()

if __name__ == '__main__':
	print('This is used for test.')
	_x = ['x = disjoint_set(*range(10))',
	'x.union(0, 2)',
	'print(x.is_same(0, 2), x.is_same(0, 3))',
	'print(x)',
	'x.union(2, 3)',
	'print(x.is_same(0, 2), x.is_same(0, 3))',
	'print(x)',
	]
	for _i in _x:
		print(f'{_i}: ', end = '')
		print(exec(_i))