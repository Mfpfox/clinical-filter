'''
Copyright (c) 2016 Genome Research Ltd.

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
of the Software, and to permit persons to whom the Software is furnished to do
so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
'''

import unittest
from clinicalfilter.ped import Family
from clinicalfilter.variant.info import Info
from clinicalfilter.variant.snv import SNV
from clinicalfilter.variant.cnv import CNV
from clinicalfilter.trio_genotypes import TrioGenotypes
from clinicalfilter.post_inheritance_filter import PostInheritanceFilter

class TestPostInheritanceFilterPy(unittest.TestCase):
    """
    """
    
    def setUp(self):
        """ define a default variant object
        """
        
        Info.populations = ['AFR_AF']
        
        family = Family('test')
        family.add_child('child', 'mother', 'father', 'male', '2', 'child_vcf')
        family.add_mother('mother', '0', '0', 'female', '1', 'mother_vcf')
        family.add_father('father', '0', '0', 'male', '2', 'father_vcf')
        family.set_child()
        
        self.variants = []
        snv = self.create_var("1", True)
        cnv = self.create_var("1", False)
        
        self.variants.append((snv, ["single_variant"], ["Monoallelic"], ["ATRX"]))
        self.variants.append((cnv, ["single_variant"], ["Monoallelic"], ["ATRX"]))
        
        self.post_filter = PostInheritanceFilter(family)
    
    def tearDown(self):
        Info.populations = []
    
    def create_var(self, chrom, snv=True, geno=["0/1", "0/1", "0/1"], info=None,
            pos='150', **kwargs):
        """ define a family and variant, and start the Inheritance class
        
        Args:
            chrom: string for chrom, since we check the number of different chroms
            snv: boolean for whether to create a SNV or CNV object
        """
        
        # generate a test variant
        if snv:
            child = self.create_snv(chrom, geno[0], info, **kwargs)
            mom = self.create_snv(chrom, geno[1], info, **kwargs)
            dad = self.create_snv(chrom, geno[2], info, **kwargs)
        else:
            child = self.create_cnv(chrom, info, **kwargs)
            mom = self.create_cnv(chrom, info, **kwargs)
            dad = self.create_cnv(chrom, info, **kwargs)
        
        return TrioGenotypes(chrom, pos, child, mom, dad)
    
    def create_snv(self, chrom, geno="0/1", info=None, pos='150',
            snp_id='.', ref='A', alt='G', qual='1000', filt='PASS', **kwargs):
        
        if info is None:
            info = "HGNC=ATRX;CQ=missense_variant;random_tag;AF_AFR=0.0001"
        
        keys = "GT:DP:TEAM29_FILTER:PP_DNM"
        values = "{0}:50:PASS:0.99".format(geno)
        
        return SNV(chrom, pos, snp_id, ref, alt, qual, filt, info=info, format=keys,
            sample=values, gender='male', **kwargs)
    
    def create_cnv(self, chrom, info=None, pos='15000000', snp_id='.', ref='A',
            alt='<DUP>', qual='1000', filt='PASS', **kwargs):
        
        if info is None:
            info = "HGNC=TEST;HGNC_ALL=TEST,OR5A1;CQ=missense_variant;CNSOLIDATE;' \
                'WSCORE=0.5;CALLP=0.000;COMMONFORWARDS=0.000;MEANLR2=0.5;' \
                'MADL2R=0.02;END=16000000;SVLEN=1000000"
        
        keys = "inheritance:DP"
        values = "deNovo:50"
        
        return CNV(chrom, pos, snp_id, ref, alt, qual, filt, info=info, format=keys,
            sample=values, gender='male', **kwargs)
    
    def test_filter_variants(self):
        """ test that filter_variants() works correctly
        
        We only need to make a quick check of the first couple of lines, since
        the called functions are themselves tested elsewhere
        """
        
        variants = [(self.create_var("1", snv=False), ["single_variant"],
            ["Biallelic"], ["ATRX"])]
        variants.append((self.create_var("2", snv=False), ["single_variant"],
            ["Biallelic"], ["ATRX"]))
        
        # check that if we have CNVs on two chroms pass the filter
        self.assertEqual(self.post_filter.filter_variants(variants), variants)
        
        # check that CNVs on three different chroms get filtered out
        variants.append((self.create_var("3", snv=False), ["single_variant"],
            ["Biallelic"], ["ATRX"]))
        self.assertEqual(self.post_filter.filter_variants(variants), [])
    
    def test_count_cnv_chroms(self):
        """ test that count_cnv_chroms() works correctly
        """
        
        # check that the default list of variants counts only one chrom
        variants = self.variants
        self.assertEqual(self.post_filter.count_cnv_chroms(variants), 1)
        
        # add CNVs on the same chrom, and check the chrom count increments one
        chrom_2_cnv_1 = self.create_var("2", snv=False)
        chrom_2_cnv_2 = self.create_var("2", snv=False)
        chrom_2_cnv_3 = self.create_var("2", snv=False)
        variants.append((chrom_2_cnv_1, ["single_variant"], ["Biallelic"], ["ATRX"]))
        variants.append((chrom_2_cnv_2, ["single_variant"], ["Biallelic"], ["ATRX"]))
        variants.append((chrom_2_cnv_3, ["single_variant"], ["Biallelic"], ["ATRX"]))
        self.assertEqual(self.post_filter.count_cnv_chroms(variants), 2)
        
        # and a CNV on a third chrom makes three
        chrom_3_cnv = self.create_var("3", snv=False)
        variants.append((chrom_3_cnv, ["single_variant"], ["Biallelic"], ["ATRX"]))
        self.assertEqual(self.post_filter.count_cnv_chroms(variants), 3)
    
    def test_remove_cnvs(self):
        """ test that remove_cnvs() works correctly
        """
        
        mixed_list = self.variants
        snv_list = [mixed_list[0]]
        cnv_list = [mixed_list[1]]
        
        # check the effect of removing CNVs on different combinations of vars
        self.assertEqual(self.post_filter.remove_cnvs(mixed_list), snv_list)
        self.assertEqual(self.post_filter.remove_cnvs(snv_list), snv_list)
        self.assertEqual(self.post_filter.remove_cnvs(cnv_list), [])
    
    def test_filter_by_maf(self):
        """ test that filter_by_maf() works correctly
        """
        
        snv_1 = self.create_var("1", snv=True)
        snv_2 = self.create_var("2", snv=True)
        
        snv_1.child.info["AFR_AF"] = 0.0001
        snv_2.child.info["AFR_AF"] = 0.002
        
        # low maf Biallelic var returns the same
        variants = [(snv_1, ["single_variant"], ["Biallelic"], ["ATRX"])]
        self.assertEqual(self.post_filter.filter_by_maf(variants), variants)
        
        # low maf non-biallelic var returns the same
        variants = [(snv_1, ["single_variant"], ["Monoallelic"], ["ATRX"])]
        self.assertEqual(self.post_filter.filter_by_maf(variants), variants)
        
        # high maf Biallelic var returns the same
        variants = [(snv_2, ["single_variant"], ["Monoallelic"], ["ATRX"])]
        self.assertEqual(self.post_filter.filter_by_maf(variants), [])
        
        # high maf non-Biallelic is filtered out
        variants = [(snv_2, ["single_variant"], ["Biallelic"], ["ATRX"])]
        self.assertEqual(self.post_filter.filter_by_maf(variants), variants)
        
        # var with multiple inheritance modes should drop the non-biallelic
        # mode if the var has a high maf (leaving the Biallelic mode)
        variants = [(snv_2, ["single_variant"], ["Monoallelic", "Biallelic"], ["ATRX"])]
        expected = [(snv_2, ["single_variant"], ["Biallelic"], ["ATRX"])]
        self.assertEqual(self.post_filter.filter_by_maf(variants), expected)
        
        # var with multiple inheritance modes should keep the non-biallelic
        # mode if the var has a low maf
        variants = [(snv_1, ["single_variant"], ["Monoallelic", "Biallelic"], ["ATRX"])]
        self.assertEqual(self.post_filter.filter_by_maf(variants), variants)
        
        # check a de novo (lacking any MAF values)
        del snv_1.child.info["AFR_AF"]
        variants = [(snv_1, ["single_variant"], ["Monoallelic"], ["ATRX"])]
        self.assertEqual(self.post_filter.filter_by_maf(variants), variants)
    
    def test_filter_by_maf_without_parents(self):
        """ test that filter_by_maf() works correctly when lacking parents
        """
        # create a child without parents
        self.post_filter.family.mother = None
        self.post_filter.family.father = None
        
        # create a variant with an allele frequency that will fail when lacking
        # parents
        snv = self.create_var("1", snv=True)
        snv.child.info["AFR_AF"] = 0.0002
        
        # check that a variant with an allele frequency above the without-parents
        # frequency is removed.
        variants = [(snv, ["single_variant"], ["Monoallelic"], ["ATRX"])]
        self.assertEqual(self.post_filter.filter_by_maf(variants), [])
        
        # check that a variant with an allele frequency below the without-parents
        # frequency still passes.
        snv.child.info["AFR_AF"] = 0.00005
        variants = [(snv, ["single_variant"], ["Monoallelic"], ["ATRX"])]
        self.assertEqual(self.post_filter.filter_by_maf(variants), variants)
    
    def test_get_polyphen_for_genes(self):
        """ test that get_polyphen_for_genes works correctly
        """
        
        var = self.create_var("1", snv=True, geno=["0/1", "0/0", "0/1"],
            info='HGNC=ATRX|TEST;CQ=missense_variant|synonymous;PolyPhen=probably_damaging(0.99)|benign(0.01)')
        
        # pulling the prediction for a single gene gets the correct prediction
        self.assertEqual(self.post_filter.get_polyphen_for_genes(var, ["ATRX"]),
            ["probably_damaging"])
        # pulling the prediction for a different gene gets the correct prediction
        self.assertEqual(self.post_filter.get_polyphen_for_genes(var, ["TEST"]),
            [""])
        # pulling the prediction for multiple genes gets the correct predictions
        self.assertEqual(self.post_filter.get_polyphen_for_genes(var, ["TEST", "ATRX"]),
            ["probably_damaging", ""])
        # the genes order doesn't affect the polyphen prediction order
        self.assertEqual(self.post_filter.get_polyphen_for_genes(var, ["ATRX", "TEST"]),
            ["probably_damaging", ""])
        
        # check that only having one polyphen prediction works corectly
        var = self.create_var("1", snv=True, geno=["0/1", "0/0", "0/1"],
            info='HGNC=ATRX;CQ=missense_variant|synonymous;PolyPhen=probably_damaging(0.99)')
        # extracting the polyphen works as expected
        self.assertEqual(self.post_filter.get_polyphen_for_genes(var, ["ATRX"]),
            ["probably_damaging"])
        # predcitions for a nonexistent gene should return a blank list
        self.assertEqual(self.post_filter.get_polyphen_for_genes(var, ["TEST"]),
            [])
        
        # expect a blank list if the variant lacks a polyphen prediction
        var = self.create_var("1", snv=True, geno=["0/1", "0/0", "0/1"],
            info='HGNC=ATRX')
        self.assertEqual(self.post_filter.get_polyphen_for_genes(var, ["ATRX"]),
            [])
        
        # gene symbols of None shouldn't break the code.
        var = self.create_var("1", snv=True, geno=["0/1", "0/0", "0/1"],
            info='HGNC=.|TEST;CQ=start_lost|missense_variant;PolyPhen=probably_damaging(0.99)|benign(0.01)')
        self.assertEqual(self.post_filter.get_polyphen_for_genes(var, ["TEST"]),
            ["benign"])

        #test that polyphen predcition is returned for missense_variant but not others
        var = self.create_var("1", snv=True, geno=["0/1", "0/0", "0/1"],
            info='HGNC=ATRX;CQ=missense_variant;PolyPhen=probably_damaging(0.99)')
        self.assertEqual(self.post_filter.get_polyphen_for_genes(var, ["ATRX"]),
            ["probably_damaging"])

        var = self.create_var("1", snv=True, geno=["0/1", "0/0", "0/1"],
            info='HGNC=ATRX;CQ=start_lost;PolyPhen=probably_damaging(0.99)')
        self.assertEqual(self.post_filter.get_polyphen_for_genes(var, ["ATRX"]),
            [""])
        
    
    def test_get_polyphen_for_genes_with_mnv(self):
        ''' test that get_polyphen_for_genes() works when variants are MNVs
        '''
        
        # a non-MNV variant returns 'benign'
        var = self.create_var("1", snv=True, geno=["0/1", "0/0", "0/1"],
            info='HGNC=TEST;CQ=missense_variant;PolyPhen=benign(0.01)')
        self.assertEqual(self.post_filter.get_polyphen_for_genes(var, ["TEST"]),
            ["benign"])
        
        unmodified = ['unmodified_synonymous_mnv' 'unmodified_protein_altering_mnv']
        modified = ['modified_protein_altering_mnv', 'modified_synonymous_mnv',
            'modified_stop_gained_mnv', 'masked_stop_gain_mnv', 'alternate_residue_mnv']
        
        # variants with an altering MNV code returns a 'MNV' code
        for code in modified:
            var = self.create_var("1", snv=True, geno=["0/1", "0/0", "0/1"],
                info='HGNC=TEST;CQ=missense_variant;PolyPhen=benign(0.01)', mnv_code=code)
            self.assertEqual(self.post_filter.get_polyphen_for_genes(var,
                ["TEST"]), ["mnv_candidate"])
        
        # a variant with a MNV code returns 'benign'
        for code in unmodified:
            var = self.create_var("1", snv=True, geno=["0/1", "0/0", "0/1"],
                info='HGNC=TEST;CQ=missense_variant;PolyPhen=benign(0.01)', mnv_code=code)
            self.assertEqual(self.post_filter.get_polyphen_for_genes(var,
                ["TEST"]), ["benign"])
    
    def test_filter_polyphen(self):
        """ check that filter_polyphen() works correctly
        """
        
        snv_1 = self.create_var("1", snv=True, geno=["0/1", "0/0", "0/1"], pos=1000)
        snv_2 = self.create_var("1", snv=True, geno=["0/1", "1/0", "0/1"], pos=2000)
        snv_3 = self.create_var("1", snv=True, geno=["0/1", "0/0", "0/0"], pos=3000)
        
        variants = [(snv_1, ["single_variant"], ["Biallelic"], ["ATRX"]), \
            (snv_2, ["single_variant"], ["Biallelic"], ["ATRX"])]
        
        # check that two vars without polyphen predictions pass
        self.assertEqual(self.post_filter.filter_polyphen(variants), variants)
        
        # check that two compound_hets in the same gene, with polyphen benign,
        # fail to pass the filter
        snv_1.child.info["PolyPhen"] = "benign(0.01)"
        snv_2.child.info["PolyPhen"] = "benign(0.01)"
        variants = [(snv_1, ["compound_het"], ["Biallelic"], ["ATRX"]), \
            (snv_2, ["compound_het"], ["Biallelic"], ["ATRX"])]
        self.assertEqual(self.post_filter.filter_polyphen(variants), [])
        
        # check that if one var is not benign, both compound hets fail to pass
        # the filter
        snv_2.child.info["PolyPhen"] = "probably_damaging(0.99)"
        self.assertEqual(self.post_filter.filter_polyphen(variants), [])
        
        # check that if one var lacks a polyphen value, and the other is damaging
        # both vars pass
        del snv_1.child.info["PolyPhen"]
        self.assertEqual(self.post_filter.filter_polyphen(variants), variants)
        
        # check that if both vars lack polyphen values, both vars pass
        del snv_2.child.info["PolyPhen"]
        self.assertEqual(self.post_filter.filter_polyphen(variants), variants)
        
        # check that single vars with polyphen benign fail
        snv_1.child.info["PolyPhen"] = "benign"
        variants = [(snv_1, ["single_variant"], ["Biallelic"], ["ATRX"])]
        self.assertEqual(self.post_filter.filter_polyphen(variants), [])
        
        # check if we have three compound_hets in the same gene, and one is
        # polyphen not benign, then all compound hets in the gene still pass,
        # even if two of them have polyphen benign
        snv_2.child.info["PolyPhen"] = "benign(0.01)"
        snv_3.child.info["PolyPhen"] = "probably_damaging(0.99)"
        variants = [(snv_1, ["compound_het"], ["Biallelic"], ["ATRX"]), \
            (snv_2, ["compound_het"], ["Biallelic"], ["ATRX"]), \
            (snv_3, ["compound_het"], ["Biallelic"], ["ATRX"])]
        self.assertEqual(self.post_filter.filter_polyphen(variants), [])
        
        # check if we have three compound_hets in the same gene, and two are
        # polyphen not benign, then only the two not benign compound hets pass
        snv_2.child.info["PolyPhen"] = "probably_damaging(0.99)"
        passing_vars = [(snv_2, ["compound_het"], ["Biallelic"], ["ATRX"]), \
            (snv_3, ["compound_het"], ["Biallelic"], ["ATRX"])]
        self.assertEqual(self.post_filter.filter_polyphen(variants), passing_vars)
        
        # if the variants overlap multiple genes, and one of the genes is
        # predicted as benign, make sure this doesn't stop variants passing for
        # the gene of interest if they are predicted to be damaging.
        snv_1.genes = ["ATRX", "TEST"]
        snv_2.genes = ["ATRX", "TEST"]
        snv_1.child.info["PolyPhen"] = "probably_damaging(0.99)|benign(0.01)"
        snv_2.child.info["PolyPhen"] = "probably_damaging(0.99)|probably_damaging(0.01)"
        variants = [(snv_1, ["compound_het"], ["Biallelic"], ["ATRX"]), \
            (snv_2, ["compound_het"], ["Biallelic"], ["ATRX"])]
        self.assertEqual(self.post_filter.filter_polyphen(variants), variants)
    
    def test_has_compound_match(self):
        """ check that has_compound_match() works correctly
        """
        
        snv_1 = self.create_var("1", snv=True, geno=["0/1", "0/0", "0/1"], pos=1000)
        snv_2 = self.create_var("1", snv=True, geno=["0/1", "1/0", "0/1"], pos=2000)
        snv_3 = self.create_var("1", snv=True, geno=["0/1", "0/0", "0/0"], pos=3000)
        
        variants = [(snv_1, ["compound_het"], ["Biallelic"], ["ATRX"]), \
            (snv_2, ["compound_het"], ["Biallelic"], ["ATRX"])]
        
        # check that two vars without polyphen annotations return false
        self.assertFalse(self.post_filter.has_compound_match(snv_1, "ATRX", variants))
        
        # check that two vars with polyphen benign return true
        snv_1.child.info["PolyPhen"] = "benign(0.01)"
        snv_2.child.info["PolyPhen"] = "benign(0.01)"
        self.assertTrue(self.post_filter.has_compound_match(snv_1, "ATRX", variants))
        
        # check that having one var not polyphen benign returns True
        snv_2.child.info["PolyPhen"] = "probably_damaging(0.99)"
        self.assertTrue(self.post_filter.has_compound_match(snv_1, "ATRX", variants))
        
        # check that, if there are more than two compound hets to check in the
        # gene, we need two passing variants in order to pass
        snv_2.child.info["PolyPhen"] = "benign(0.01)"
        variants = [(snv_1, ["compound_het"], ["Biallelic"], ["ATRX"]), \
            (snv_2, ["compound_het"], ["Biallelic"], ["ATRX"]),
            (snv_3, ["compound_het"], ["Biallelic"], ["ATRX"])]
        self.assertTrue(self.post_filter.has_compound_match(snv_1, "ATRX", variants))
        
        # check that if we are checking a benign variant, and there are more
        # than two compound hets to check in the gene, if we have more than
        # two non-benign variants would prevent a match, then the function
        # returns false
        snv_1.child.info["PolyPhen"] = "probably_damaging(0.99)"
        variants = [(snv_1, ["compound_het"], ["Biallelic"], ["ATRX"]), \
            (snv_2, ["compound_het"], ["Biallelic"], ["ATRX"]),
            (snv_3, ["compound_het"], ["Biallelic"], ["ATRX"])]
        self.assertFalse(self.post_filter.has_compound_match(snv_1, "ATRX", variants))
        
        # check that single variants in the same gene still return True
        variants = [(snv_1, ["compound_het"], ["Biallelic"], ["ATRX"]), \
            (snv_2, ["single_variant"], ["Biallelic"], ["ATRX"])]
        self.assertFalse(self.post_filter.has_compound_match(snv_1, "ATRX", variants))
    
    def test_has_compound_match_proband_only(self):
        """ check that has_compound_match() works correctly without parents
        """
        
        snv_1 = self.create_var("1", snv=True, geno=["0/1", "0/0", "0/1"], pos=1000)
        snv_2 = self.create_var("1", snv=True, geno=["0/1", "1/0", "0/1"], pos=2000)
        
        snv_1.mother = None
        snv_1.father = None
        snv_2.mother = None
        snv_2.father = None
        
        variants = [(snv_1, ["compound_het"], ["Biallelic"], ["ATRX"]), \
            (snv_2, ["compound_het"], ["Biallelic"], ["ATRX"])]
        
        # check that two vars without polyphen annotations return false
        self.assertFalse(self.post_filter.has_compound_match(snv_1, "ATRX", variants))
    
    def test_filter_exac(self):
        """ check that filter_exac() works correctly
        """
        
        # construct a variant that will pass
        var = self.create_var("1", snv=True, geno=["0/1", "0/1", "0/1"])
        variants = [(var, ["single_variant"], ["Biallelic"], ["ATRX"])]
        
        # we should get back the same list of variants, if none of them have a
        # male chrX
        self.assertEqual(self.post_filter.filter_exac(variants), variants)
        
        # now construct a male chrX variant, which contains a non-zero AC_Hemi
        # annotation. This should fail the filter
        var = self.create_var("X", snv=True, geno=["1/1", "1/1", "1/1"])
        var.child.info["AC_Hemi"] = "1"
        variants = [(var, ["single_variant"], ["Hemizygous"], ["ATRX"])]
        self.assertEqual(self.post_filter.filter_exac(variants), [])
        
        # if the variant has passed under multiple inheritance modes, then
        # we trim out the hemizygous mode, leaving the remaining modes
        variants = [(var, ["single_variant"], ["Hemizygous", "X-linked dominant"], ["ATRX"])]
        expected = [(var, ["single_variant"], ["X-linked dominant"], ["ATRX"])]
        self.assertEqual(self.post_filter.filter_exac(variants), expected)
        
        # if the AC_Hemi count is zero, this should pass the filter
        var.child.info["AC_Hemi"] = "0"
        variants = [(var, ["single_variant"], ["Hemizygous"], ["ATRX"])]
        self.assertEqual(self.post_filter.filter_exac(variants), variants)
        
        # check that chrX females with non-zero AC_Hemi counts are not excluded
        var.child.info["AC_Hemi"] = "1"
        self.post_filter.family.child.sex = "female"
        variants = [(var, ["single_variant"], ["Hemizygous"], ["ATRX"])]
        self.assertEqual(self.post_filter.filter_exac(variants), variants)
        
        # now construct a de novo male chrX variant, which contains a non-zero
        # AC_Hemi annotation. Since this is not inherited, it should pass.
        var = self.create_var("X", snv=True, geno=["1/1", "0/0", "0/0"])
        var.child.info["AC_Hemi"] = "1"
        self.post_filter.family.child.sex = "male"
        variants = [(var, ["single_variant"], ["Hemizygous"], ["ATRX"])]
        self.assertEqual(self.post_filter.filter_exac(variants), variants)
    
    def test_filter_exac_monoallelic(self):
        """ check filter_exac() under monoallelic inheritance
        """
        
        # construct a monoallelic variant that will pass
        var = self.create_var("1", snv=True, geno=["0/1", "0/1", "0/1"])
        var.child.info["AC_Het"] = "4"
        variants = [(var, ["single_variant"], ["Monoallelic"], ["ATRX"])]
        self.assertEqual(self.post_filter.filter_exac(variants), variants)
        
        # construct a monoallelic variant that will fail
        var = self.create_var("1", snv=True, geno=["0/1", "0/1", "0/1"])
        var.child.info["AC_Het"] = "5"
        variants = [(var, ["single_variant"], ["Monoallelic"], ["ATRX"])]
        self.assertEqual(self.post_filter.filter_exac(variants), [])
        
        # construct a variant that will fail
        var = self.create_var("1", snv=True, geno=["0/1", "0/0", "0/0"])
        var.child.info["AC_Het"] = "5"
        variants = [(var, ["single_variant"], ["Monoallelic"], ["ATRX"])]
        self.assertEqual(self.post_filter.filter_exac(variants), [])
        
        # if the variant has passed under multiple inheritance modes, then
        # we trim out the monoallelic mode, leaving the remaining modes
        variants = [(var, ["single_variant"], ["Monoallelic", "Biallelic"], ["ATRX"])]
        expected = [(var, ["single_variant"], ["Biallelic"], ["ATRX"])]
        self.assertEqual(self.post_filter.filter_exac(variants), expected)
    
    def test_filter_exac_x_linked_dominant(self):
        """check filter_exac() under X-linked dominant inheritance
        """
        
        # check that X-linked dominant variants pass when the allele count is low
        var = self.create_var("X", snv=True, geno=["1/1", "1/1", "1/1"])
        var.child.info["AC_Het"] = "4"
        variants = [(var, ["single_variant"], ["X-linked dominant"], ["ATRX"])]
        self.assertEqual(self.post_filter.filter_exac(variants), variants)
        
        # check that X-linked dominant variants fail when the het count is high
        var = self.create_var("X", snv=True, geno=["1/1", "1/1", "1/1"])
        var.child.info["AC_Het"] = "5"
        variants = [(var, ["single_variant"], ["X-linked dominant"], ["ATRX"])]
        self.assertEqual(self.post_filter.filter_exac(variants), [])
        
        # check that X-linked dominant variants fail when the hemi count is high
        var = self.create_var("X", snv=True, geno=["1/1", "1/1", "1/1"])
        var.child.info["AC_Hemi"] = "5"
        variants = [(var, ["single_variant"], ["X-linked dominant"], ["ATRX"])]
        self.assertEqual(self.post_filter.filter_exac(variants), [])
        
        # check that X-linked dominant variants fail when neither the het or
        # hemi count on their own are too high, but combined they exceed the threshold
        var = self.create_var("X", snv=True, geno=["1/1", "1/1", "1/1"])
        var.child.info["AC_Het"] = "3"
        var.child.info["AC_Hemi"] = "3"
        variants = [(var, ["single_variant"], ["X-linked dominant"], ["ATRX"])]
        self.assertEqual(self.post_filter.filter_exac(variants), [])
        
        # check that X-linked dominant variants fail multi-allelic sites
        # combined exceed the threshold
        var = self.create_var("X", snv=True, geno=["1/1", "1/1", "1/1"])
        var.child.info["AC_Hemi"] = "3,3"
        variants = [(var, ["single_variant"], ["X-linked dominant"], ["ATRX"])]
        self.assertEqual(self.post_filter.filter_exac(variants), [])
        
        
        
