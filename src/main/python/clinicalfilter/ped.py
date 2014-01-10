""" A class for loading ped files, and sorting the lines into families
"""

import os
import logging
import sys

class person(object):
    """creates an object for a person, with their ID, and path to their VCF file etc
    """
    def __init__(self, person_ID, VCF_path, affected_status, gender):
        self.person_ID = person_ID
        self.VCF_path = VCF_path
        self.gender = gender
        self.affected_status = affected_status
        
        # set a flag so we can check whether the child has been analysed
        self.analysed = False
        
        # define some codes used in ped files to identify male and female sexes
        self.male_codes = set(["1", "m", "M", "male"])
        self.female_codes = set(["2", "f", "F", "female"])
    
    def get_ID(self):
        """returns the ID for a person.
        """
        return self.person_ID
    
    def get_path(self):
        """returns the path to the VCF file for a person.
        """
        return self.VCF_path
    
    def get_affected_status(self):
        """returns the affected status for a person as a string
        """
        return self.affected_status
    
    def is_affected(self):
        """gets a boolean value for affected status, rather than the affected status string
        """
        # change how the affected status is encoded. Current DDD ped files encode from "1" for 
        # unaffected, and "2" for affected. Change this to True/False values, and catch any unknown 
        # affected statuses.
        if self.affected_status == "1":
            boolean_affected_status = False
        elif self.affected_status == "2":
            boolean_affected_status = True
        else:
            sys.exit("unknown affected: " + self.affected_status + ", should be 1 = unaffected, 2 = affected") 
        
        return boolean_affected_status
    
    def get_gender(self):
        """returns the gender for a person (1, M = male, 2, F = female).
        """
        return self.gender
    
    def is_male(self):
        """ returns True/False for whether the person is male
        """
        
        return self.get_gender() in self.male_codes
    
    def is_female(self):
        """ returns True/False for whether the person is male
        """
        
        return self.get_gender() in self.female_codes
    
    def check_gender(self, gender_code):
        """ makes sure that the parents match their expected gender.
        
        Args:
            gender_code: mothers, being female, are "2", while fathers, being male, are "1"
        """
        
        if self.is_male():
            current_gender_codes = self.male_codes
        elif self.is_female():
            current_gender_codes = self.female_codes
        else:
            sys.exit("unknown gender code: " + self.get_gender())
        
        if gender_code not in current_gender_codes:
            print(current_gender_codes)
            # I'm logging this, as well as exiting with a message, do we need both?
            logging.warning(self.person_ID + "'s gender differs from that expected as a parent")
            sys.exit(self.person_ID + " is listed as gender " + self.get_gender() + ", which " \
                     + "is different to that expected from their parental status (ie mother or " \
                     + "father)")

class pedTrio(person):
    """creates an object for each trio, with useful info like paths, IDs, and affected statuses.
    """
    
    def __init__(self, family_ID):
        """ initiates the class with the ID for the family
        """
        self.family_ID = family_ID
        self.children = []
        self.father = None
        self.mother = None
    
    def has_child(self):
        """ Check whether a childs details have been included.
        """
        if len(self.children) == 0:
            return True
        else:
            return False
    
    def add_child(self, ID, path, affected_status, gender):
        tmp_child = person(ID, path, affected_status, gender)
        tmp_child.analysed = False
        self.children.append(tmp_child)
    
    def add_mother(self, ID, path, affected_status, gender):
        self.mother = person(ID, path, affected_status, gender)
        self.mother.check_gender("2")
    
    def add_father(self, ID, path, affected_status, gender):
        self.father = person(ID, path, affected_status, gender)
        self.father.check_gender("1")
    
    def set_child(self):
        """set the child as the first in the family without a 'True' examined status
        """
        for child in self.children:
            if child.analysed == False:
                self.child = child
                break
    
    def set_child_examined(self):
        """ once a child has been examined, mark it as such in the list of children
        """
        for child_position in range(len(self.children)):
            child = self.children[child_position]
            if child.get_ID() == self.child.get_ID():
                self.children[child_position].analysed = True
    
    def check_all_children_analysed(self):
        """returns whether all the children in a family have been analysed
        """
        all_checked = True
        for child in self.children:
            if child.analysed == False:
                all_checked = False
        
        return all_checked
    
    def has_sibling(self):
        if len(self.children) == 1:
            return False
        else:
            return True
    
    # def swap_sibling_to_child(self):
    #     self.set_child(self.sibling.get_ID(), self.sibling.get_path(), self.sibling.get_affected_status(), self.sibling.get_gender())
    
    def get_trio_paths(self):
        return [self.child.get_path(), self.mother.get_path(), self.father.get_path()]
    
    def get_parents_affected_status(self):
        """ Determine whether either, or both, of the parents are also affected.
        
        Returns:
            the affected status of the parents as a string.
        """
        
        # account for how the parents affected status changes the chromosome inheritance model
        mother_affected = self.mother.is_affected() 
        father_affected = self.father.is_affected()
        
        if not mother_affected and not father_affected:
            affected_status = "parents_unaffected"
        elif mother_affected and not father_affected:
            affected_status = "mother_affected"
        elif not mother_affected and father_affected:
            affected_status = "father_affected"
        elif mother_affected and father_affected:
            affected_status = "both_parents_affected"
        else:
            print("unknown parental affected status, mother:", mother_affected, \
                  "father:", father_affected, ". They should be True/False values")
            sys.exit(1)
        
        return affected_status

def loadPedFile(path):
    """Loads a PED file containing details for multiple trios.
    
    The PED file is in LINKAGE PED format, with the first six columns specfifying the indivudual and
    how they are related to toher individuals. In contrast to other PED files, the genotypes are 
    specified as a path to a VCF file for the individual.
    
    Args:
        path: path to the ped file
    
    Returns:
        mothers: dictionary of maternal IDs, indexed by the childs ID
        fathers: dictionary of paternal IDs, indexed by the childs ID
        children: dictionary of family IDs, indexed by the childs ID
        affected: dictionary of affected statuses, indexed by individual ID
        sex: dictionary of genders, indexed by individual ID
        vcfs: dictionary of VCF paths, indexed by individual ID
    
    Raises:
        IOError: an error when the PED file path is not specified correctly
    """
    
    if not os.path.exists(path):
        print(path)
        raise IOError("Path to ped file does not exist")
    
    mothers = {}
    fathers = {}
    children = {}
    affected = {}
    sex = {}
    vcfs = {}
    
    f = open(path, "r")
    for line in f:
        line = line.strip().split()
        
        family_ID = line[0]
        individual_ID = line[1]
        paternal_ID = line[2]
        maternal_ID = line[3]
        gender = line[4]
        affected_status = line[5]
        path = line[6]
        
        # make sure we can match each individual to their own paths, and affected status
        vcfs[individual_ID] = path
        affected[individual_ID] = affected_status
        sex[individual_ID] = gender
        
        # track the child, maternal and paternal IDs
        if paternal_ID != '0' and maternal_ID != '0':
            children[individual_ID] = family_ID
        if paternal_ID != 0:
            fathers[individual_ID] = paternal_ID
        if maternal_ID != 0:
            mothers[individual_ID] = maternal_ID
    
    return mothers, fathers, children, affected, sex, vcfs

def loadPedTrios(path):
    """Creates a dictionary of trio data from a PED file.
    
    Args:
        path: path to the ped file
        
    Returns:
        pedTrios: a dictionary of pedTrio objects, indexed by family IDs
    """
    
    # do an initial parse of the ped file
    mothers, fathers, children, affected, sex, vcfs = loadPedFile(path)
    
    pedTrios = {}
    
    # put all the family info into a trio class
    for child_ID, family_ID in children.items():
        # if the family hasn't been included already, generate a new class for the trio
        if family_ID not in pedTrios:
            pedTrios[family_ID] = pedTrio(family_ID)
        
        trio = pedTrios[family_ID]
        father = fathers[child_ID]
        mother = mothers[child_ID]
        
        # add the child to the family, and set the child to be examined
        trio.add_child(child_ID, vcfs[child_ID], affected[child_ID], sex[child_ID])
        trio.set_child()
        
        # add parents, but allow for children without parents listed in the ped file
        if father in vcfs and father in affected:
            trio.add_father(father, vcfs[father], affected[father], sex[father])
        if mother in vcfs and mother in affected:
            trio.add_mother(mother, vcfs[mother], affected[mother], sex[mother])
        
        pedTrios[family_ID] = trio
    
    return pedTrios
