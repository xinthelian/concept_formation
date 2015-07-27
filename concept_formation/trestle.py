from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

from concept_formation.utils import weighted_choice
from concept_formation.cobweb3 import Cobweb3Tree
from concept_formation.cobweb3 import Cobweb3Node
from concept_formation.cobweb3 import ContinuousValue
from concept_formation.structure_mapper import StructureMapper

class TrestleTree(Cobweb3Tree):
    """
    The TrestleTree instantiates the Trestle algorithm, which can
    be used to learn from and categorize instances. Trestle adds the ability to
    handle component attributes as well as relations in addition to the
    numerical and nominal attributes of Cobweb and Cobweb/3.

    .. todo:: Not sure this is articulated quite right.

    Attributes are interpreted in the following ways
        * Numeric - ``isinstance(instance[attr],Number) == True``
        * Nominal - everything else, though the assumption is
            ``isinstance(instance[attr],str) == True``
        * Relation - ``isinstance(attr, tuple)`` after the attribute has been
            tuplized (e.g., input attr = "(before o1 o2)").
        * Component - Any attributes or values that begin with a '?'.
    """

    def __init__(self, alpha=0.001, scaling=True):
        """
        The tree constructor. 

        The alpha parameter is the parameter used for laplacian smoothing of
        nominal values (or whether an attribute is present or not for both
        nominal and numeric attributes). The higher the value, the higher the
        prior that all attributes/values are equally likely. By default a minor
        smoothing is used: 0.001.

        .. todo:: Need to test scaling by 1 std vs. 2 std. It might be
            preferrable to standardize by 2 std because that gives it the same
            variance as a nominal value.
            
        The scaling parameter determines whether online normalization of
        continuous attributes is used. By default scaling is used. Scaling
        divides the std of each attribute by the std of the attribute in the
        parent node (no scaling is performed in the root). Scaling is useful to
        balance the weight of different numerical attributes, without scaling
        the magnitude of numerical attributes can affect category utility
        calculation meaning numbers that are naturally larger will recieve
        extra weight in the calculation.

        :param alpha: constant to use for laplacian smoothing.
        :type alpha: float
        :param scaling: whether or not numerical values should be scaled in
        online normalization.
        :type scaling: bool
        """
        self.root = Cobweb3Node()
        self.root.tree = self
        self.alpha = alpha
        self.scaling = scaling
        self.std_to_scale= 1.0

    def clear(self):
        """
        Clears the concepts stored in the tree, but maintains the alpha and
        scaling parameters.
        """
        self.root = Cobweb3Node()
        self.root.tree = self

    def ifit(self, instance):
        """
        Incrementally fit a new instance into the tree and return its resulting
        concept.

        The instance is passed down the tree and updates each node to
        incorporate the instance. This process modifies the trees knowledge;
        for a non-modifying version use the categorize() function.

        This version is modified from the normal :meth:`CobwebTree.ifit
        <concept_formation.cobweb.CobwebTree.ifit>` by first structure mapping
        the instance before fitting it into the knoweldge base.
        
        :param instance: an instance to be categorized into the tree.
        :type instance: {a1:v1, a2:v2, ...}
        :return: A concept describing the instance
        :rtype: Cobweb3Node

        .. note:: this modifies the tree's knoweldge.
        .. seealso:: :meth:`TrestleTree.trestle`
        """
        return self.trestle(instance)

    def _trestle_categorize(self, instance):
        """
        The structure maps the instance, categorizes the matched instance, and
        returns the resulting Cobweb3Node.

        :param instance: an instance to be categorized into the tree.
        :type instance: {a1:v1, a2:v2, ...}
        :return: A concept describing the instance
        :rtype: Cobweb3Node
        """
        structure_mapper = StructureMapper(self.root)
        temp_instance = structure_mapper.transform(instance)
        return self._cobweb_categorize(temp_instance)

    def infer_missing(self, instance, choice_fn="most likely"):
        """
        Given a tree and an instance, returns a new instance with attribute 
        values picked using the specified choice function (wither "most likely"
        or "sampled"). 

        :param instance: an instance to be completed.
        :type instance: {a1: v1, a2: v2, ...}
        :param choice_fn: a string specifying the choice function to use,
            either "most likely" or "sampled". 
        :type choice_fn: a string
        :return: A completed instance
        :rtype: instance
        """
        structure_mapper = StructureMapper(self.root)
        temp_instance = structure_mapper.transform(instance)
        temp_instance = super(TrestleTree, self).infer_missing(temp_instance, choice_fn)
        return structure_mapper.undo_transform(temp_instance)

    def categorize(self, instance):
        """
        Sort an instance in the categorization tree and return its resulting
        concept.

        The instance is passed down the the categorization tree according to the
        normal cobweb algorithm except using only the new and best opperators
        and without modifying nodes' probability tables.

        This version differs fomr the normal :meth:`CobwebTree.categorize
        <concept_formation.cobweb.CobwebTree.categorize>` and
        :meth:`Cobweb3Tree.categorize
        <concept_formation.cobweb3.Cobweb3Tree.categorize>` by structure mapping
        instances before categorizing them.

        :param instance: an instance to be categorized into the tree.
        :type instance: {a1:v1, a2:v2, ...}
        :return: A concept describing the instance
        :rtype: CobwebNode

        .. note:: this does not modify the tree's knoweldge.
        .. seealso:: :meth:`TrestleTree.trestle`
        """
        return self._trestle_categorize(instance)

    def trestle(self, instance):
        """
        The core trestle algorithm used in fitting and categorization.

        This function is similar to :meth:`Cobweb.cobweb
        <concept_formation.cobweb.CobwebTree.cobweb>` The key difference
        between trestle and cobweb is that trestle performs structure mapping
        (see: :meth:`structure_map
        <concept_formation.structure_mapper.structure_map>`) before proceeding
        through the normal cobweb algorithm.

        :param instance: an instance to be categorized into the tree.
        :type instance: {a1:v1, a2:v2, ...}
        :return: A concept describing the instance
        :rtype: CobwebNode
        """
        structure_mapper = StructureMapper(self.root)
        temp_instance = structure_mapper.transform(instance)
        return self.cobweb(temp_instance)
