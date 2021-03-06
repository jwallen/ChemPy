#!/usr/bin/env python
# -*- coding: utf-8 -*-

################################################################################
#
#   ChemPy - A chemistry toolkit for Python
#
#   Copyright (c) 2010 by Joshua W. Allen (jwallen@mit.edu)
#
#   Permission is hereby granted, free of charge, to any person obtaining a
#   copy of this software and associated documentation files (the 'Software'),
#   to deal in the Software without restriction, including without limitation
#   the rights to use, copy, modify, merge, publish, distribute, sublicense,
#   and/or sell copies of the Software, and to permit persons to whom the
#   Software is furnished to do so, subject to the following conditions:
#
#   The above copyright notice and this permission notice shall be included in
#   all copies or substantial portions of the Software.
#
#   THE SOFTWARE IS PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#   IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#   FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#   AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#   LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#   FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#   DEALINGS IN THE SOFTWARE.
#
################################################################################

"""
This module contains classes and functions for working with chemical reactions.

From the `IUPAC Compendium of Chemical Terminology 
<http://dx.doi.org/10.1351/goldbook>`_, a chemical reaction is "a process that 
results in the interconversion of chemical species".

In ChemPy, a chemical reaction is called a Reaction object and is represented in
memory as an instance of the :class:`Reaction` class.
"""

import cython
import math
import numpy

import constants
from exception import ChemPyError

from species import Species
from kinetics import ArrheniusModel

################################################################################

class ReactionError(Exception):
    """
    An exception class for exceptional behavior involving :class:`Reaction`
    objects. In addition to a string `message` describing the exceptional
    behavior, this class stores the `reaction` that caused the behavior.
    """
    def __init__(self, reaction, message=''):
        self.reaction = reaction
        self.message = message

    def __str__(self):
        string = "Reaction: "+str(self.reaction) + '\n'
        for reactant in self.reaction.reactants:
            string += reactant.toAdjacencyList() + '\n'
        for product in self.reaction.products:
            string += product.toAdjacencyList() + '\n'
        if self.message: string += "Message: "+self.message
        return string

################################################################################

class Reaction:
    """
    A chemical reaction.
    
    =================== =========================== ============================
    Attribute           Type                        Description
    =================== =========================== ============================
    `index`             :class:`int`                A unique nonnegative integer index
    `reactants`         :class:`list`               The reactant species (as :class:`Species` objects)
    `products`          :class:`list`               The product species (as :class:`Species` objects)
    `kinetics`          :class:`KineticsModel`      The kinetics model to use for the reaction
    `reversible`        ``bool``                    ``True`` if the reaction is reversible, ``False`` if not
    `transitionState`   :class:`TransitionState`    The transition state
    `thirdBody`         ``bool``                    ``True`` if the reaction if the reaction kinetics imply a third body, ``False`` if not
    =================== =========================== ============================
    
    """
    
    def __init__(self, index=-1, reactants=None, products=None, kinetics=None, reversible=True, transitionState=None, thirdBody=False):
        self.index = index
        self.reactants = reactants
        self.products = products
        self.kinetics = kinetics
        self.reversible = reversible
        self.transitionState = transitionState
        self.thirdBody = thirdBody

    def __repr__(self):
        """
        Return a string representation of the reaction, suitable for console output.
        """
        return "<Reaction %i '%s'>" % (self.index, str(self))
    
    def __str__(self):
        """
        Return a string representation of the reaction, in the form 'A + B <=> C + D'.
        """
        arrow = ' <=> '
        if not self.reversible: arrow = ' -> '
        return arrow.join([' + '.join([str(s) for s in self.reactants]), ' + '.join([str(s) for s in self.products])])

    def hasTemplate(self, reactants, products):
        """
        Return ``True`` if the reaction matches the template of `reactants`
        and `products`, which are both lists of :class:`Species` objects, or
        ``False`` if not.
        """
        return ((all([spec in self.reactants for spec in reactants]) and
            all([spec in self.products for spec in products])) or
            (all([spec in self.products for spec in reactants]) and
            all([spec in self.reactants for spec in products])))

    def getEnthalpyOfReaction(self, T):
        """
        Return the enthalpy of reaction in J/mol evaluated at temperature
        `T` in K.
        """
        cython.declare(dHrxn=cython.double, reactant=Species, product=Species)
        dHrxn = 0.0
        for reactant in self.reactants:
            dHrxn -= reactant.thermo.getEnthalpy(T)
        for product in self.products:
            dHrxn += product.thermo.getEnthalpy(T)
        return dHrxn

    def getEntropyOfReaction(self, T):
        """
        Return the entropy of reaction in J/mol*K evaluated at temperature `T`
        in K.
        """
        cython.declare(dSrxn=cython.double, reactant=Species, product=Species)
        dSrxn = 0.0
        for reactant in self.reactants:
            dSrxn -= reactant.thermo.getEntropy(T)
        for product in self.products:
            dSrxn += product.thermo.getEntropy(T)
        return dSrxn

    def getFreeEnergyOfReaction(self, T):
        """
        Return the Gibbs free energy of reaction in J/mol evaluated at
        temperature `T` in K.
        """
        cython.declare(dGrxn=cython.double, reactant=Species, product=Species)
        dGrxn = 0.0
        for reactant in self.reactants:
            dGrxn -= reactant.thermo.getFreeEnergy(T)
        for product in self.products:
            dGrxn += product.thermo.getFreeEnergy(T)
        return dGrxn

    def getEquilibriumConstant(self, T, type='Kc'):
        """
        Return the equilibrium constant for the reaction at the specified
        temperature `T` in K. The `type` parameter lets	you specify the
        quantities used in the equilibrium constant: ``Ka`` for	activities,
        ``Kc`` for concentrations (default), or ``Kp`` for pressures. Note that
        this function currently assumes an ideal gas mixture.
        """
        cython.declare(dGrxn=cython.double, K=cython.double, C0=cython.double, P0=cython.double)
        # Use free energy of reaction to calculate Ka
        dGrxn = self.getFreeEnergyOfReaction(T)
        K = numpy.exp(-dGrxn / constants.R / T)
        # Convert Ka to Kc or Kp if specified
        P0 = 1e5
        if type == 'Kc':
            # Convert from Ka to Kc; C0 is the reference concentration
            C0 = P0 / constants.R / T
            K *= C0 ** (len(self.products) - len(self.reactants))
        elif type == 'Kp':
            # Convert from Ka to Kp; P0 is the reference pressure
            K *= P0 ** (len(self.products) - len(self.reactants))
        elif type != 'Ka' and type != '':
            raise ChemPyError('Invalid type "%s" passed to Reaction.getEquilibriumConstant(); should be "Ka", "Kc", or "Kp".')
        return K

    def getEnthalpiesOfReaction(self, Tlist):
        """
        Return the enthalpies of reaction in J/mol evaluated at temperatures
        `Tlist` in K.
        """
        return numpy.array([self.getEnthalpyOfReaction(T) for T in Tlist], numpy.float64)

    def getEntropiesOfReaction(self, Tlist):
        """
        Return the entropies of reaction in J/mol*K evaluated at temperatures
        `Tlist` in K.
        """
        return numpy.array([self.getEntropyOfReaction(T) for T in Tlist], numpy.float64)

    def getFreeEnergiesOfReaction(self, Tlist):
        """
        Return the Gibbs free energies of reaction in J/mol evaluated at
        temperatures `Tlist` in K.
        """
        return numpy.array([self.getFreeEnergyOfReaction(T) for T in Tlist], numpy.float64)

    def getEquilibriumConstants(self, Tlist, type='Kc'):
        """
        Return the equilibrium constants for the reaction at the specified
        temperatures `Tlist` in K. The `type` parameter lets you specify the
        quantities used in the equilibrium constant: ``Ka`` for	activities,
        ``Kc`` for concentrations (default), or ``Kp`` for pressures. Note that
        this function currently assumes an ideal gas mixture.
        """
        return numpy.array([self.getEquilibriumConstant(T, type) for T in Tlist], numpy.float64)

    def getStoichiometricCoefficient(self, spec):
        """
        Return the stoichiometric coefficient of species `spec` in the reaction.
        The stoichiometric coefficient is increased by one for each time `spec`
        appears as a product and decreased by one for each time `spec` appears
        as a reactant.
        """
        cython.declare(stoich=cython.int, reactant=Species, product=Species)
        stoich = 0
        for reactant in self.reactants:
            if reactant is spec: stoich -= 1
        for product in self.products:
            if product is spec: stoich += 1
        return stoich

    def getRate(self, T, P, conc, totalConc=-1.0):
        """
        Return the net rate of reaction at temperature `T` and pressure `P`. The
        parameter `conc` is a map with species as keys and concentrations as
        values. A reactant not found in the `conc` map is treated as having zero
        concentration.

        If passed a `totalConc`, it won't bother recalculating it.
        """

        cython.declare(rateConstant=cython.double, equilibriumConstant=cython.double)
        cython.declare(forward=cython.double, reverse=cython.double, speciesConc=cython.double)

        # Calculate total concentration
        if totalConc == -1.0:
            totalConc=sum( conc.values() )

        # Evaluate rate constant
        rateConstant = self.kinetics.getRateCoefficient(T, P)
        if self.thirdBody: rateConstant *= totalConc

        # Evaluate equilibrium constant
        equilibriumConstant = self.getEquilibriumConstant(T)

        # Evaluate forward concentration product
        forward = 1.0
        for reactant in self.reactants:
            if reactant in conc:
                speciesConc = conc[reactant]
                forward = forward * speciesConc
            else:
                forward = 0.0
                break

        # Evaluate reverse concentration product
        reverse = 1.0
        for product in self.products:
            if product in conc:
                speciesConc = conc[product]
                reverse = reverse * speciesConc
            else:
                reverse = 0.0
                break

        # Return rate
        return rateConstant * (forward - reverse / equilibriumConstant)

    def generateReverseRateCoefficient(self, Tlist):
        """
        Generate and return a rate coefficient model for the reverse reaction
        using a supplied set of temperatures `Tlist`. Currently this only
        works if the `kinetics` attribute is an :class:`ArrheniusModel` object.
        """
        if not isinstance(self.kinetics, ArrheniusModel):
            raise ReactionError("ArrheniusModel kinetics required to use Reaction.generateReverseRateCoefficient(), but %s object encountered." % (self.kinetics.__class__))

        cython.declare(klist=numpy.ndarray, i=cython.int, kf=ArrheniusModel, kr=ArrheniusModel)
        kf = self.kinetics

        # Determine the values of the reverse rate coefficient k_r(T) at each temperature
        klist = numpy.zeros_like(Tlist)
        for i in range(len(Tlist)):
            klist[i] = kf.getRateCoefficient(Tlist[i]) / self.getEquilibriumConstant(Tlist[i])

        # Fit and return an Arrhenius model to the k_r(T) data
        kr = ArrheniusModel()
        kr.fitToData(Tlist, klist, kf.T0)
        return kr

    def calculateTSTRateCoefficients(self, Tlist, tunneling=''):
        return numpy.array([self.calculateTSTRateCoefficient(T, tunneling) for T in Tlist], numpy.float64)

    def calculateTSTRateCoefficient(self, T, tunneling=''):
        """
        Evaluate the forward rate coefficient for the reaction with
        corresponding transition state `TS` at temperature `T` in K using
        (canonical) transition state theory. The TST equation is

        .. math:: k(T) = \\kappa(T) \\frac{k_\\mathrm{B} T}{h} \\frac{Q^\\ddagger(T)}{Q^\\mathrm{A}(T) Q^\\mathrm{B}(T)} \\exp \\left( -\\frac{E_0}{k_\\mathrm{B} T} \\right)

        where :math:`Q^\\ddagger` is the partition function of the transition state,
        :math:`Q^\\mathrm{A}` and :math:`Q^\\mathrm{B}` are the partition function
        of the reactants, :math:`E_0` is the ground-state energy difference from
        the transition state to the reactants, :math:`T` is the absolute
        temperature, :math:`k_\\mathrm{B}` is the Boltzmann constant, and :math:`h`
        is the Planck constant. :math:`\\kappa(T)` is an optional tunneling
        correction.
        """
        cython.declare(E0=cython.double)
        # Determine barrier height
        E0 = self.transitionState.E0 - sum([spec.E0 for spec in self.reactants])
        # Determine TST rate constant at each temperature
        Qreac = 1.0
        for spec in self.reactants: Qreac *= spec.states.getPartitionFunction(T) / (constants.R * T / 1e5)
        Qts = self.transitionState.states.getPartitionFunction(T) / (constants.R * T / 1e5)
        k = self.transitionState.degeneracy * (constants.kB * T / constants.h * Qts / Qreac *	numpy.exp(-E0 / constants.R / T))
        # Apply tunneling correction
        if tunneling.lower() == 'wigner':
            k *= self.calculateWignerTunnelingCorrection(T)
        elif tunneling.lower() == 'eckart':
            k *= self.calculateEckartTunnelingCorrection(T)
        return k
    
    def calculateWignerTunnelingCorrection(self, T):
        """
        Calculate and return the value of the Wigner tunneling correction for
        the reaction with corresponding transition state `TS` at the list of
        temperatures `Tlist` in K. The Wigner formula is
        
        .. math:: \\kappa(T) = 1 + \\frac{1}{24} \\left( \\frac{h | \\nu_\\mathrm{TS} |}{ k_\\mathrm{B} T} \\right)^2
        
        where :math:`h` is the Planck constant, :math:`\\nu_\\mathrm{TS}` is the
        negative frequency, :math:`k_\\mathrm{B}` is the Boltzmann constant, and
        :math:`T` is the absolute temperature. 
        The Wigner correction only requires information about the transition 
        state, not the reactants or products, but is also generally less 
        accurate than the Eckart correction.
        """
        frequency = abs(self.transitionState.frequency)
        return 1.0 + (constants.h * constants.c * 100.0 * frequency / constants.kB / T)**2 / 24.0
    
    def calculateEckartTunnelingCorrection(self, T):
        """
        Calculate and return the value of the Eckart tunneling correction for
        the reaction with corresponding transition state `TS` at the list of
        temperatures `Tlist` in K. The Eckart formula is
        
        .. math:: \\kappa(T) = e^{\\beta \\Delta V_1} \\int_0^\\infty 
            \\left[ 1 - \\frac{\\cosh (2 \\pi a - 2 \\pi b) + \\cosh (2 \\pi d)}{\\cosh (2 \\pi a + 2 \\pi b) + \\cosh (2 \\pi d)} \\right] e^{- \\beta E} \\ d(\\beta E)
        
        where
        
        .. math:: 2 \\pi a = \\frac{2 \\sqrt{\\alpha_1 \\xi}}{\\alpha_1^{-1/2} + \\alpha_2^{-1/2}}
        
        .. math:: 2 \\pi b = \\frac{2 \\sqrt{| (\\xi - 1) \\alpha_1 + \\alpha_2|}}{\\alpha_1^{-1/2} + \\alpha_2^{-1/2}}
        
        .. math:: 2 \\pi d = 2 \\sqrt{| \\alpha_1 \\alpha_2 - 4 \\pi^2 / 16|}
        
        .. math:: \\alpha_1 = 2 \\pi \\frac{\\Delta V_1}{h | \\nu_\\mathrm{TS} |}
        
        .. math:: \\alpha_2 = 2 \\pi \\frac{\\Delta V_2}{h | \\nu_\\mathrm{TS} |}
        
        .. math:: \\xi = \\frac{E}{\\Delta V_1}
        
        :math:`\\Delta V_1` and :math:`\\Delta V_2` are the thermal energy 
        difference between the transition state and the reactants and products,
        respectively; :math:`\\nu_\\mathrm{TS}` is the negative frequency, 
        :math:`h` is the Planck constant, :math:`k_\\mathrm{B}` is the 
        Boltzmann constant, and :math:`T` is the absolute temperature. If 
        product data is not available, then it is assumed that 
        :math:`\\alpha_2 \\approx \\alpha_1`.
        The Eckart correction requires information about the reactants as well
        as the transition state. For best results, information about the 
        products should also be given. (The former is called the symmetric
        Eckart correction, the latter the asymmetric Eckart correction.) This
        extra information allows the Eckart correction to generally give a
        better result than the Wignet correction.
        """
        
        cython.declare(frequency=cython.double, alpha1=cython.double, alpha2=cython.double, dV1=cython.double, dV2=cython.double)
        cython.declare(kappa=cython.double, E_kT=numpy.ndarray, f=numpy.ndarray, integral=cython.double)
        cython.declare(i=cython.int, tol=cython.double, fcrit=cython.double, E_kTmin=cython.double, E_kTmax=cython.double)
        
        frequency = abs(self.transitionState.frequency)
        
        # Calculate intermediate constants
        dV1 = self.transitionState.E0 - sum([spec.E0 for spec in self.reactants]) # [=] J/mol
        #if all([spec.states is not None for spec in self.products]):
            # Product data available, so use asymmetric Eckart correction
        dV2 = self.transitionState.E0 - sum([spec.E0 for spec in self.products]) # [=] J/mol
        #else:
            ## Product data not available, so use asymmetric Eckart correction
            #dV2 = dV1
        # Tunneling must be done in the exothermic direction, so swap if this 
        # isn't the case
        if dV2 < dV1: dV1, dV2 = dV2, dV1
        alpha1 = 2 * math.pi * dV1 / constants.Na / (constants.h * constants.c * 100.0 * frequency)
        alpha2 = 2 * math.pi * dV2 / constants.Na / (constants.h * constants.c * 100.0 * frequency)
        
        # Integrate to get Eckart correction
        kappa = 0.0
        
        # First we need to determine the lower and upper bounds at which to
        # truncate the integral
        tol = 1e-3
        E_kT = numpy.arange(0.0, 1000.01, 0.1)
        f = numpy.zeros_like(E_kT)
        for j in range(len(E_kT)):
            f[j] = self.__eckartIntegrand(E_kT[j], constants.R * T, dV1, alpha1, alpha2)
        # Find the cutoff values of the integrand
        fcrit = tol * f.max()
        x = (f > fcrit).nonzero()
        E_kTmin = E_kT[x[0][0]]
        E_kTmax = E_kT[x[0][-1]]

        # Now that we know the bounds we can formally integrate
        import scipy.integrate
        integral = scipy.integrate.quad(self.__eckartIntegrand, E_kTmin, E_kTmax,
            args=(constants.R * T,dV1,alpha1,alpha2,))[0]
        kappa = integral * math.exp(dV1 / constants.R / T)
        
        # Return the calculated Eckart correction
        return kappa
    
    def __eckartIntegrand(self, E_kT, kT, dV1, alpha1, alpha2):
        # Evaluate the integrand of the Eckart tunneling correction integral
        # for the given values
        #    E_kT = energy scaled by kB * T (dimensionless)
        #    kT = Boltzmann constant * T [=] J/mol
        #    dV1 = energy difference between TS and reactants [=] J/mol
        #    alpha1, alpha2 dimensionless
        
        cython.declare(xi=cython.double, twopia=cython.double, twopib=cython.double, twopid=cython.double, kappaE=cython.double)
        from math import sqrt, exp, cosh, pi
        
        xi = E_kT * kT / dV1
        # 2 * pi * a
        twopia = 2*sqrt(alpha1*xi)/(1/sqrt(alpha1)+1/sqrt(alpha2))
        # 2 * pi * b
        twopib = 2*sqrt(abs((xi-1)*alpha1+alpha2))/(1/sqrt(alpha1)+1/sqrt(alpha2))
        # 2 * pi * d
        twopid = 2*sqrt(abs(alpha1*alpha2-4*pi*pi/16))
        
        # We use different approximate versions of the integrand to avoid
        # domain errors when evaluating cosh(x) for large x
        # If all of 2*pi*a, 2*pi*b, and 2*pi*d are sufficiently small,
        # compute as normal
        if twopia < 200 and twopib < 200 and twopid < 200:
            kappaE = 1 - (cosh(twopia-twopib)+cosh(twopid)) / (cosh(twopia+twopib)+cosh(twopid))
        # If one of the following is true, then we can eliminate most of the
        # exponential terms after writing out the definition of cosh and
        # dividing all terms by exp(2*pi*d)
        elif twopia-twopib-twopid > 10 or twopib-twopia-twopid > 10 or twopia+twopib-twopid > 10:
            kappaE = 1 - exp(-2*twopia) - exp(-2*twopib) - exp(-twopia-twopib+twopid) - exp(-twopia-twopib-twopid)
        # Otherwise expand each cosh(x) in terms of its exponentials and divide
        # all terms by exp(2*pi*d) before evaluating
        else:
            kappaE = 1 - (exp(twopia-twopib-twopid) + exp(-twopia+twopib-twopid) + 1 + exp(-2*twopid)) / (exp(twopia+twopib-twopid) + exp(-twopia-twopib-twopid) + 1 + exp(-2*twopid))

        # Complete and return integrand
        return exp(-E_kT) * kappaE
    
################################################################################

class ReactionModel:
    """
    A chemical reaction model, composed of a list of species and a list of
    reactions.

    =============== =========================== ================================
    Attribute       Type                        Description
    =============== =========================== ================================
    `species`       :class:`list`               The species involved in the reaction model
    `reactions`     :class:`list`               The reactions comprising the reaction model
    `stoichiometry` :class:`numpy.ndarray`      The stoichiometric matrix for the reaction model, stored as a sparse matrix
    =============== =========================== ================================

    """

    def __init__(self, species=None, reactions=None):
        self.species = species or []
        self.reactions = reactions or []
        self.stoichiometry = None

    def generateStoichiometryMatrix(self):
        """
        Generate the stoichiometry matrix corresponding to the current
        reaction system. The stoichiometry matrix is defined such that the
        rows correspond to the `index` attribute of each species object, while
        the columns correspond to the `index` attribute of each reaction object.
        The generated matrix is not returned, but is instead stored in the
        `stoichiometry` attribute for future use.
        """
        cython.declare(rxn=Reaction, spec=Species, i=cython.int, j=cython.int, nu=cython.int)
        from scipy import sparse

        # Use dictionary-of-keys format to efficiently assemble stoichiometry matrix
        self.stoichiometry = sparse.dok_matrix((len(self.species), len(self.reactions)), numpy.float64)
        for rxn in self.reactions:
            j = rxn.index - 1
            # Only need to iterate over the species involved in the reaction,
            # not all species in the reaction model
            for spec in rxn.reactants:
                i = spec.index - 1
                nu = rxn.getStoichiometricCoefficient(spec)
                if nu != 0: self.stoichiometry[i,j] = nu
            for spec in rxn.products:
                i = spec.index - 1
                nu = rxn.getStoichiometricCoefficient(spec)
                if nu != 0: self.stoichiometry[i,j] = nu

        # Convert to compressed-sparse-row format for efficient use in matrix operations
        self.stoichiometry.tocsr()

    def getReactionRates(self, T, P, Ci):
        """
        Return an array of reaction rates for each reaction in the model core
        and edge. The id of the reaction is the index into the vector.
        """
        cython.declare(rxnRates=numpy.ndarray, rxn=Reaction, j=cython.int)
        rxnRates = numpy.zeros(len(self.reactions), numpy.float64)
        for rxn in self.reactions:
            j = rxn.index - 1
            rxnRates[j] = rxn.getRate(T, P, Ci)
        return rxnRates

