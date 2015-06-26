""" unit testing of the VcfInfo class
"""

import unittest

from clinicalfilter.variant.snv import SNV

class TestVariantInfoPy(unittest.TestCase):
    """
    """
    
    def setUp(self):
        """ define a default VcfInfo object
        """
        
        chrom = "1"
        pos = "15000000"
        snp_id = "CM00001"
        ref = "A"
        alt = "G"
        filt = "PASS"
        
        # set up a SNV object, since SNV inherits VcfInfo
        self.var = SNV(chrom, pos, snp_id, ref, alt, filt)
        self.var.debug_chrom = "1"
        self.var.debug_pos = "15000000"
        
        self.default_info = "HGNC=ATRX;CQ=missense_variant;random_tag"
        
        
        # here are the default filtering criteria, as loaded into python
        known_genes = {"ATRX": {"inheritance": {"Hemizygous": \
            {"Loss of function"}}, "start": "10000000", "chrom": "1", \
            "confirmed_status": {"Confirmed DD Gene"}, "end": "20000000"}}
        
        SNV.known_genes = known_genes
        
        self.var.add_info(self.default_info)
    
    def test_set_gene_from_info(self):
        """ test that test_set_gene_from_info() works correctly
        """
        
        # check for when a HGNC key exists
        self.var.info["HGNC"] = "A"
        self.var.set_gene_from_info()
        self.assertEqual(self.var.gene, ["A"])
        
        # check for when a HGNC key doesn't exist
        del self.var.info["HGNC"]
        self.var.set_gene_from_info()
        self.assertIsNone(self.var.gene)
    
    def test_is_lof(self):
        """ test that is_lof() works correctly
        """
        
        # check that known LOF consensequence return True
        self.var.consequence = ["stop_gained"]
        self.assertTrue(self.var.is_lof())
        
        # check that known non-LOF consensequence returns False
        self.var.consequence = ["missense_variant"]
        self.assertFalse(self.var.is_lof())
        
        # check that null values return False
        self.var.consequence = None
        self.assertFalse(self.var.is_lof())
        
        # check when the variant overlaps multiple genes (so has multiple
        # gene symbols and consequences).
        self.var.consequence = ["stop_gained", "missense_variant"]
        self.var.gene = ["ATRX", "TTN"]
        self.assertTrue(self.var.is_lof())
        self.assertTrue(self.var.is_lof("ATRX"))
        self.assertFalse(self.var.is_lof("TTN"))
    
    def test_get_most_severe_consequence(self):
        """ test that get_most_severe_consequence works correctly
        """
        
        # check for the most simple list
        cq = ["missense_variant", "splice_acceptor_variant"]
        self.assertEqual(self.var.get_most_severe_consequence(cq), \
            "splice_acceptor_variant")
        
        # check for a single-entry list
        cq = ["missense_variant"]
        self.assertEqual(self.var.get_most_severe_consequence(cq), "missense_variant")
        
        # check for lists of lists per allele
        cq_per_allele = [["synonymous_variant", "splice_donor_variant"], \
            ["missense_variant", "regulatory_region_variant"]]
        self.assertEqual(self.var.get_most_severe_consequence(cq_per_allele), \
            ["missense_variant", "splice_donor_variant"])
    
    def test_get_per_gene_consequence(self):
        """ test that get_per_gene_consequence works correctly
        """
        
        self.var.gene = ["ATRX"]
        self.var.consequence = ["missense_variant"]
        
        self.assertEqual(self.var.get_per_gene_consequence(None), ["missense_variant"])
        self.assertEqual(self.var.get_per_gene_consequence("ATRX"), ["missense_variant"])
        self.assertEqual(self.var.get_per_gene_consequence("TEST"), [])
        
        # check a variant with consequences in multiple genes, that we only
        # pull out the consequencesquences for a single gene
        self.var.gene = ["ATRX", "TTN"]
        self.var.consequence = ["missense_variant", "synonymous_variant"]
        self.assertEqual(self.var.get_per_gene_consequence("ATRX"), ["missense_variant"])
        self.assertEqual(self.var.get_per_gene_consequence("TTN"), ["synonymous_variant"])
        
        # check a symbol where two symbols are blank (ie no HGNC symbol, which
        # indicates the other genes have VEGA, ENGSG, or ENSR symbols)
        self.var.gene = ["", "ATRX", ""]
        self.var.consequence = ["splice_acceptor_variant", "missense_variant", \
            "synonymous_variant"]
        self.assertEqual(self.var.get_per_gene_consequence(""), \
            ["splice_acceptor_variant", "synonymous_variant"])
        
    def test_get_allele_frequency(self):
        """ tests that number conversion works as expected
        """
        
        # single number returns that number
        self.assertEqual(self.var.get_allele_frequency("1"), 1)
        
        # two numbers return one number
        self.assertEqual(self.var.get_allele_frequency("1,1"), 1)
        
        # two numbers return the highest number
        self.assertEqual(self.var.get_allele_frequency("1,2"), 2)
        
        # number and string return the number
        self.assertEqual(self.var.get_allele_frequency("a,1"), 1)
        
        # single string value returns None
        self.assertEqual(self.var.get_allele_frequency("a"), None)
        
        # multiple string values return None
        self.assertEqual(self.var.get_allele_frequency("a,b"), None)
    
    def test_is_number(self):
        """ tests that we can check if a value represents a number
        """
        
        self.assertEqual(self.var.is_number(None), False)
        self.assertEqual(self.var.is_number("5"), True)
        self.assertEqual(self.var.is_number("a"), False)
    
    def test_find_max_allele_frequency(self):
        """ test if the MAF finder operates correctly
        """
        
        # check for var without recorded MAF
        self.assertIsNone(self.var.find_max_allele_frequency())
        
        # check for single population
        self.var.info["MAX_AF"] = "0.005"
        self.assertEqual(self.var.find_max_allele_frequency(), 0.005)
        
        # check for two populations
        self.var.info["AFR_AF"] = "0.01"
        self.assertEqual(self.var.find_max_allele_frequency(), 0.01)
        
        # check for all populations
        pops = set(["AFR_AF", "AMR_AF", "ASN_AF", "DDD_AF", "EAS_AF", \
            "ESP_AF", "EUR_AF", "MAX_AF", "SAS_AF", "UK10K_cohort_AF"])
        for pop in pops:
            self.var.info[pop] = "0.05"
            self.assertEqual(self.var.find_max_allele_frequency(), 0.05)
    
    


if __name__ == '__main__':
    unittest.main()
