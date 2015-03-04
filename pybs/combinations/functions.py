from operator import __mul__
from itertools import product
from pybs.utils import ClonableMultiset as Multiset, memoized
from pybs.unordered_tree import UnorderedTree, leaf
from pybs.combinations import LinearCombination, Forest as Forest
from pybs.combinations import Forest as FrozenForest  # TODO: NASTY HACK
from pybs.combinations import empty_tree


@memoized
def graft(base, other):  # TODO: change order of base and other. Fix all uses too!
    result = LinearCombination()
    if base == empty_tree():
        result += other
        return result
    elif other == empty_tree():
        result += base
        return result
    else:
        result += base.butcher_product(other)
        for subtree, multiplicity1 in base.items():
            amputated_tree = base.sub(subtree)
            replacements = graft(subtree, other)
            for replacement, multiplicity2 in replacements.items():
                new_tree = amputated_tree.add(replacement)
                result[new_tree] += multiplicity1 * multiplicity2
        return result


def split(tree, truncate=False):
    "Splits a tree."  # TODO: Check that this is the right way around!!!!!!
    result = _split(tree)
    if not truncate:
        result[(tree, empty_tree())] = 1
    return result


def _split(tree):
    result = LinearCombination()
    for childtree, multiplicity in tree.items():
        amputated_tree = tree.sub(childtree)
        result[(childtree, amputated_tree)] = multiplicity
        childSplits = _split(childtree)
        for pair, multiplicity2 in childSplits.items():
            new_tree = amputated_tree.add(pair[1])
            new_pair = (pair[0], new_tree)
            result[new_pair] = multiplicity * multiplicity2
    return result


def symp_split(tree):
    result = LinearCombination()
    for childtree, multiplicity in tree.items():
        amputated_tree = tree.sub(childtree)
        if childtree == leaf():
            result[amputated_tree] += multiplicity
        else:
            child_splits = symp_split(childtree)
            for tree2, multiplicity2 in child_splits.items():
                new_tree = amputated_tree.add(tree2)
                result[new_tree] += multiplicity * multiplicity2
    return result


def subtrees(tree):  # HCK comporudct.
    result = LinearCombination()
    if tree == empty_tree():
        result += (empty_tree(), empty_tree())
        return result  # TODO: IS THIS NECESSARY?
    result[(Forest((tree,)), empty_tree())] = 1
    tmp = [subtrees(child_tree) for child_tree in tree.elements()]  # TODO: more efficient looping.
    if tmp:
        tmp2 = [elem.items() for elem in tmp]  # TODO: Try using iterators.
        for item in product(*tmp2):  # iterator over all combinations.
            tensorproducts, factors = zip(*item)
            multiplicity = 1
            for factor in factors:
                multiplicity *= factor
            cuttings, to_be_grafted = zip(*tensorproducts)
            with Forest().clone() as forest_of_cuttings:
                for forest in cuttings:
                    forest_of_cuttings.inplace_multiset_sum(forest)
            result[(forest_of_cuttings, UnorderedTree(to_be_grafted))] += multiplicity
    else:
        result[(empty_tree(), tree)] = 1
    return result


def _subtrees_for_antipode(tree):
    result = LinearCombination()
    tmp = [subtrees(child_tree) for child_tree in tree.elements()]  # TODO: more efficient looping.
    if tmp:
        tmp2 = [elem.items() for elem in tmp]  # TODO: Try using iterators.
        for item in product(*tmp2):  # iterator over all combinations.
            tensorproducts, factors = zip(*item)
            multiplicity = 1
            for factor in factors:
                multiplicity *= factor
            cuttings, to_be_grafted = zip(*tensorproducts)
            with Forest().clone() as forest_of_cuttings:
                for forest in cuttings:
                    forest_of_cuttings.inplace_multiset_sum(forest)
            result[(forest_of_cuttings, UnorderedTree(to_be_grafted))] += multiplicity
    result[(empty_tree(), tree)] = 0  # TODO: FIND NICER WAY.
    return result


# TODO: Should be memoized, but linearCOmbination is mutable.
# Make LinComb clonable??
def antipode_ck(tree):
    result = LinearCombination()
    if tree == empty_tree():
        result[empty_tree()] = 1
        return result
    elif isinstance(tree, Forest):
        result[empty_tree()] = 1
        for tree1, multiplicity in tree.items():
            for i in range(multiplicity):
                tmp = LinearCombination()
                for forest1, multiplicity1 in antipode_ck(tree1).items():
                    for forest2, multiplicity2 in result.items():
                        tmp[forest1 * forest2] += multiplicity1 * multiplicity2
                result = tmp
        return result
        # TODO: implement multiplication of LinComb.
    result[Forest((tree,))] -= 1
    for (forest, subtree), multiplicity in _subtrees_for_antipode(tree).items():
        for forest2, coefficient in antipode_ck(forest).items():
            result[forest2.add(subtree)] -= coefficient * multiplicity
    return result


def differentiate(thing):
    if isinstance(thing, LinearCombination):
        result = LinearCombination()
        for tree, factor in thing.iteritems():
            result += treeD(tree) * factor
    elif isinstance(thing, UnorderedTree):
        result = treeD(thing)
    elif thing == empty_tree():
        result = LinearCombination()
        result += leaf()
    return result


def treeD(tree):
    return graft(tree, leaf())


def linCombCommutator(op1, op2, max_order=None):
    if isinstance(op1, UnorderedTree) or op1 == empty_tree():
        tmp = LinearCombination()
        tmp += op1
        op1 = tmp
    if isinstance(op2, UnorderedTree) or op2 == empty_tree():
        tmp = LinearCombination()
        tmp += op2
        op2 = tmp
    result = LinearCombination()
    for tree1, factor1 in op1.items():
        for tree2, factor2 in op2.items():
            if (not max_order) or tree1.order() + tree2.order() <= max_order:
                result += (factor1 * factor2) * treeCommutator(tree1, tree2)
    return result


def treeCommutator(op1, op2):
    return graft(op1, op2) - graft(op2, op1)
