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

from species cimport Species, TransitionState
from kinetics cimport KineticsModel, ArrheniusModel

cimport numpy

################################################################################

cdef class Reaction:
    
    cdef public int index
    cdef public list reactants
    cdef public list products
    cdef public bint reversible
    cdef public TransitionState transitionState
    cdef public KineticsModel kinetics
    cdef public bint thirdBody

    cpdef bint hasTemplate(self, list reactants, list products)

    cpdef double getEnthalpyOfReaction(self, double T)

    cpdef double getEntropyOfReaction(self, double T)

    cpdef double getFreeEnergyOfReaction(self, double T)

    cpdef double getEquilibriumConstant(self, double T, str type=?)

    cpdef numpy.ndarray getEnthalpiesOfReaction(self, numpy.ndarray Tlist)

    cpdef numpy.ndarray getEntropiesOfReaction(self, numpy.ndarray Tlist)

    cpdef numpy.ndarray getFreeEnergiesOfReaction(self, numpy.ndarray Tlist)

    cpdef numpy.ndarray getEquilibriumConstants(self, numpy.ndarray Tlist, str type=?)

    cpdef int getStoichiometricCoefficient(self, Species spec)

    cpdef double getRate(self, double T, double P, dict conc, double totalConc=?)

    cpdef generateReverseRateCoefficient(self, numpy.ndarray Tlist)

    cpdef numpy.ndarray calculateTSTRateCoefficients(self, numpy.ndarray Tlist, str tunneling=?)

    cpdef double calculateTSTRateCoefficient(self, double T, str tunneling=?)
    
    cpdef double calculateWignerTunnelingCorrection(self, double T)
    
    cpdef double calculateEckartTunnelingCorrection(self, double T)

    cpdef double __eckartIntegrand(self, double E_kT, double kT, double dV1, double alpha1, double alpha2)

################################################################################

cdef class ReactionModel:

    cdef public list species
    cdef public list reactions

    cpdef generateStoichiometryMatrix(self)

    cpdef numpy.ndarray getReactionRates(self, double T, double P, dict Ci)

################################################################################
