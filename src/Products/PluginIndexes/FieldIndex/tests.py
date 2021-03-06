##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""FieldIndex unit tests.
"""

import unittest

from Products.PluginIndexes.FieldIndex.FieldIndex import FieldIndex


class Dummy(object):

    def __init__(self, foo):
        self._foo = foo

    def foo(self):
        return self._foo

    def __str__(self):
        return '<Dummy: %s>' % self._foo

    __repr__ = __str__


class FieldIndexTests(unittest.TestCase):
    """Test FieldIndex objects.
    """

    def setUp(self):
        self._index = FieldIndex('foo')
        self._marker = []
        self._values = [(0, Dummy('a')),
                        (1, Dummy('ab')),
                        (2, Dummy('abc')),
                        (3, Dummy('abca')),
                        (4, Dummy('abcd')),
                        (5, Dummy('abce')),
                        (6, Dummy('abce')),
                        (7, Dummy(0))]
        self._forward = {}
        self._backward = {}
        for k, v in self._values:
            self._backward[k] = v
            keys = self._forward.get(v, [])
            self._forward[v] = keys

        self._noop_req  = {'bar': 123}
        self._request   = {'foo': 'abce'}
        self._min_req   = {'foo':
            {'query': 'abc', 'range': 'min'}}
        self._min_req_n = {'foo':
            {'query': 'abc', 'range': 'min', 'not': 'abca'}}
        self._max_req   = {'foo':
            {'query': 'abc', 'range': 'max'}}
        self._max_req_n = {'foo':
            {'query': 'abc', 'range': 'max', 'not': ['a', 'b', 0]}}
        self._range_req = {'foo':
            {'query': ('abc', 'abcd'), 'range': 'min:max'}}
        self._range_ren = {'foo':
            {'query': ('abc', 'abcd'), 'range': 'min:max', 'not': 'abcd'}}
        self._range_non = {'foo':
            {'query': ('a', 'aa'), 'range': 'min:max', 'not': 'a'}}
        self._zero_req  = {'foo': 0 }
        self._not_1     = {'foo': {'query': 'a', 'not': 'a'}}
        self._not_2     = {'foo': {'query': ['a', 'ab'], 'not': 'a'}}
        self._not_3     = {'foo': {'not': 'a'}}
        self._not_4     = {'foo': {'not': [0]}}
        self._not_5     = {'foo': {'not': ['a', 'b']}}
        self._not_6     = {'foo': 'a', 'bar': {'query': 123, 'not': 1}}

    def _populateIndex(self):
        for k, v in self._values:
            self._index.index_object(k, v)

    def _checkApply(self, req, expectedValues):
        result, used = self._index._apply_index(req)
        if hasattr(result, 'keys'):
            result = result.keys()
        assert used == ('foo', )
        assert len(result) == len(expectedValues), \
          '%s | %s' % (map(None, result), expectedValues)
        for k, v in expectedValues:
            assert k in result

    def test_interfaces(self):
        from Products.PluginIndexes.interfaces import IPluggableIndex
        from Products.PluginIndexes.interfaces import ISortIndex
        from Products.PluginIndexes.interfaces import IUniqueValueIndex
        from zope.interface.verify import verifyClass

        verifyClass(IPluggableIndex, FieldIndex)
        verifyClass(ISortIndex, FieldIndex)
        verifyClass(IUniqueValueIndex, FieldIndex)

    def testEmpty(self):
        "Test an empty FieldIndex."

        assert len(self._index) == 0
        assert len(self._index.referencedObjects()) == 0
        self.assertEqual(self._index.numObjects(), 0)

        assert self._index.getEntryForObject(1234) is None
        assert (self._index.getEntryForObject(1234, self._marker)
                  is self._marker)
        self._index.unindex_object(1234)  # nothrow

        assert self._index.hasUniqueValuesFor('foo')
        assert not self._index.hasUniqueValuesFor('bar')
        assert len(list(self._index.uniqueValues('foo'))) == 0

        assert self._index._apply_index(self._noop_req) is None
        self._checkApply(self._request, [])
        self._checkApply(self._min_req, [])
        self._checkApply(self._min_req_n, [])
        self._checkApply(self._max_req, [])
        self._checkApply(self._max_req_n, [])
        self._checkApply(self._range_req, [])
        self._checkApply(self._range_ren, [])
        self._checkApply(self._range_non, [])

    def testPopulated(self):
        """ Test a populated FieldIndex """
        self._populateIndex()
        values = self._values

        assert len(self._index) == len(values) - 1  # 'abce' is duplicate
        assert len(self._index.referencedObjects() ) == len(values)
        self.assertEqual(self._index.indexSize(), len(values) - 1)

        assert self._index.getEntryForObject(1234) is None
        assert (self._index.getEntryForObject(1234, self._marker)
                  is self._marker)
        self._index.unindex_object(1234)  # nothrow

        for k, v in values:
            assert self._index.getEntryForObject(k) == v.foo()

        assert len(list(self._index.uniqueValues('foo'))) == len(values) - 1

        assert self._index._apply_index(self._noop_req) is None

        self._checkApply(self._request, values[-3:-1])
        self._checkApply(self._min_req, values[2:-1])
        self._checkApply(self._min_req_n, values[2:3] + values[4:-1])
        self._checkApply(self._max_req, values[:3] + values[-1:])
        self._checkApply(self._max_req_n, values[1:3])
        self._checkApply(self._range_req, values[2:5])
        self._checkApply(self._range_ren, values[2:4])
        self._checkApply(self._range_non, [])

        self._checkApply(self._not_1, [])
        self._checkApply(self._not_2, values[1:2])
        self._checkApply(self._not_3, values[1:])
        self._checkApply(self._not_4, values[:7])
        self._checkApply(self._not_5, values[1:])
        self._checkApply(self._not_6, values[0:1])

    def testZero(self):
        """ Make sure 0 gets indexed """
        self._populateIndex()
        values = self._values
        self._checkApply(self._zero_req, values[-1:])
        assert 0 in self._index.uniqueValues('foo')

    def testNone(self):
        # make sure None cannot get indexed
        try:
            self._index.index_object(10, Dummy(None))
        except TypeError as exc:
            self.assertEqual(exc.message, 'None cannot be indexed.')
        else:
            self.assertTrue(False, 'TypeError not raised')

        try:
            self._checkApply({'foo': None}, [])
        except TypeError as exc:
            self.assertEqual(exc.message, 'None cannot be in an index.')
        else:
            self.assertTrue(False, 'TypeError not raised')

        self.assertFalse(None in self._index.uniqueValues('foo'))

    def testReindex(self):
        self._populateIndex()
        result, used = self._index._apply_index({'foo': 'abc'})
        assert list(result) == [2]
        assert self._index.keyForDocument(2) == 'abc'
        d = Dummy('world')
        self._index.index_object(2, d)
        result, used = self._index._apply_index({'foo': 'world'})
        assert list(result) == [2]
        assert self._index.keyForDocument(2) == 'world'
        del d._foo
        self._index.index_object(2, d)
        result, used = self._index._apply_index({'foo': 'world'})
        assert list(result) == []
        try:
            should_not_be = self._index.keyForDocument(2)
        except KeyError:
            # As expected, we deleted that attribute.
            pass
        else:
            # before Collector #291 this would be 'world'
            raise ValueError(repr(should_not_be))

    def testRange(self):
        """Test a range search"""
        index = FieldIndex('foo')
        for i in range(100):
            index.index_object(i, Dummy(i % 10))

        record = {'foo': {'query': [-99, 3], 'range': 'min:max'}}
        r = index._apply_index(record)

        assert tuple(r[1]) == ('foo', ), r[1]
        r = list(r[0].keys())

        expect = [
            0, 1, 2, 3, 10, 11, 12, 13, 20, 21, 22, 23, 30, 31, 32, 33,
            40, 41, 42, 43, 50, 51, 52, 53, 60, 61, 62, 63, 70, 71, 72, 73,
            80, 81, 82, 83, 90, 91, 92, 93
            ]
        assert r == expect, r

        # Make sure that range tests with incompatible paramters
        # don't return empty sets.
        record['foo']['operator'] = 'and'
        r2, ignore = index._apply_index(record)
        r2 = list(r2.keys())
        assert r2 == r
