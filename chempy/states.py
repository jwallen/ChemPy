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
Each atom in a molecular configuration has three spatial dimensions in which it
can move. Thus, a molecular configuration consisting of :math:`N` atoms has
:math:`3N` degrees of freedom. We can distinguish between those modes that
involve movement of atoms relative to the molecular center of mass (called
*internal* modes) and those that do not (called *external* modes). Of the
external degrees of freedom, three involve translation of the entire molecular
configuration, while either three (for a nonlinear molecule) or two (for a
linear molecule) involve rotation of the entire molecular configuration
around the center of mass. The remaining :math:`3N-6` (nonlinear) or
:math:`3N-5` (linear) degrees of freedom are the internal modes, and can be
divided into those that involve vibrational motions (symmetric and asymmetric
stretches, bends, etc.) and those that involve torsional rotation around single
bonds between nonterminal heavy atoms.

The mathematical description of these degrees of freedom falls under the purview
of quantum chemistry, and involves the solution of the time-independent
Schrodinger equation:

    .. math:: \\hat{H} \\psi = E \\psi

where :math:`\\hat{H}` is the Hamiltonian, :math:`\\hat{H}` is the wavefunction,
and :math:`E` is the energy. The exact form of the Hamiltonian varies depending
on the degree of freedom you are modeling. Since this is a quantum system, the
energy can only take on discrete values. Once the allowed energy levels are
known, the partition function :math:`Q(\\beta)` can be computed using the
summation

    .. math:: Q(\\beta) = \\sum_i g_i e^{-\\beta E_i}

where :math:`g_i` is the degeneracy of energy level :math:`i` (i.e. the number
of energy states at that energy level) and
:math:`\\beta \\equiv (k_\\mathrm{B} T)^{-1}`.

The partition function is an immensely useful quantity, as all sorts of
thermodynamic parameters can be evaluated using the partition function:

    .. math:: A = - k_\\mathrm{B} T \\ln Q

    .. math:: U = - \\frac{\\partial \\ln Q}{\\partial \\beta}

    .. math:: S = \\frac{\\partial}{\\partial T} \\left( k_\\mathrm{B} T \\ln Q \\right)

    .. math:: C_\\mathrm{v} = \\frac{1}{k_\\mathrm{B} T} \\frac{\\partial^2 \\ln Q}{\\partial \\beta^2}

Above, :math:`A`, :math:`U`, :math:`S`, and :math:`C_\\mathrm{v}` are the
Helmholtz free energy, internal energy, entropy, and constant-volume heat
capacity, respectively.

The partition function for a molecular configuration is the product of the
partition functions for each invidual degree of freedom:

    .. math:: Q = Q_\\mathrm{trans} Q_\\mathrm{rot} Q_\\mathrm{vib} Q_\\mathrm{tors} Q_\\mathrm{elec}

This means that the contributions to each thermodynamic quantity from each
molecular degree of freedom are additive.

This module contains models for various molecular degrees of freedom. All such
models derive from the :class:`Mode` base class. A list of molecular degrees of
freedom can be stored in a :class:`StatesModel` object.
"""

################################################################################

import math
import cython
import numpy

import constants
from exception import InvalidStatesModelError

################################################################################

class Mode:

    def getPartitionFunctions(self, Tlist):
        return numpy.array([self.getPartitionFunction(T) for T in Tlist], numpy.float64)

    def getHeatCapacities(self, Tlist):
        return numpy.array([self.getHeatCapacity(T) for T in Tlist], numpy.float64)

    def getEnthalpies(self, Tlist):
        return numpy.array([self.getEnthalpy(T) for T in Tlist], numpy.float64)

    def getEntropies(self, Tlist):
        return numpy.array([self.getEntropy(T) for T in Tlist], numpy.float64)

################################################################################

class Translation(Mode):
    """
    A representation of translational motion in three dimensions for an ideal
    gas. The `mass` attribute is the molar mass of the molecule in kg/mol. The
    quantities that depend on volume/pressure (partition function and entropy)
    are evaluated at a standard pressure of 1 bar.
    """

    def __init__(self, mass=0.0):
        self.mass = mass

    def __repr__(self):
        """
        Return a string representation that can be used to reconstruct the
        object.
        """
        return 'Translation(mass=%g)' % (self.mass)

    def getPartitionFunction(self, T):
        """
        Return the value of the partition function at the specified temperatures
        `Tlist` in K. The formula is

        .. math:: q_\\mathrm{trans}(T) = \\left( \\frac{2 \\pi m k_\\mathrm{B} T}{h^2} \\right)^{3/2} \\frac{k_\\mathrm{B} T}{P}

        where :math:`T` is temperature, :math:`V` is volume, :math:`m` is mass,
        :math:`d` is dimensionality, :math:`k_\\mathrm{B}` is the Boltzmann
        constant, and :math:`h` is the Planck constant.
        """
        cython.declare(qt=cython.double)
        qt = ((2 * constants.pi * self.mass / constants.Na) / (constants.h * constants.h))**1.5 / 1e5
        return qt * (constants.kB * T)**2.5

    def getHeatCapacity(self, T):
        """
        Return the contribution to the heat capacity due to translation in
        J/mol*K at the specified temperatures `Tlist` in K. The formula is

        .. math:: \\frac{C_\\mathrm{v}^\\mathrm{trans}(T)}{R} = \\frac{3}{2}

        where :math:`T` is temperature and :math:`R` is the gas law constant.
        """
        return 1.5 * constants.R

    def getEnthalpy(self, T):
        """
        Return the contribution to the enthalpy due to translation in J/mol
        at the specified temperatures `Tlist` in K. The formula is

        .. math:: \\frac{H^\\mathrm{trans}(T)}{RT} = \\frac{3}{2}

        where :math:`T` is temperature and :math:`R` is the gas law constant.
        """
        return 1.5 * constants.R * T

    def getEntropy(self, T):
        """
        Return the contribution to the entropy due to translation in J/mol*K
        at the specified temperatures `Tlist` in K. The formula	is

        .. math:: \\frac{S^\\mathrm{trans}(T)}{R} = \\ln q_\\mathrm{trans}(T) + \\frac{3}{2} + 1

        where :math:`T` is temperature, :math:`q_\\mathrm{trans}` is the
        partition function, and :math:`R` is the gas law constant.
        """
        return (numpy.log(self.getPartitionFunction(T)) + 1.5 + 1.0) * constants.R

    def getDensityOfStates(self, Elist):
        """
        Return the density of states at the specified energlies `Elist` in J/mol
        above the ground state. The formula is

        .. math:: \\rho(E) = \\left( \\frac{2 \\pi m}{h^2} \\right)^{3/2} \\frac{E^{3/2}}{\\Gamma(5/2)} \\frac{1}{P}

        where :math:`E` is energy, :math:`m` is mass, :math:`k_\\mathrm{B}` is
        the Boltzmann constant, and :math:`R` is the gas law constant.
        """
        cython.declare(rho=numpy.ndarray, qt=cython.double)
        rho = numpy.zeros_like(Elist)
        qt = ((2 * constants.pi * self.mass / constants.Na / constants.Na) / (constants.h * constants.h))**(1.5) / 1e5
        rho = qt * Elist**1.5 / (numpy.sqrt(math.pi) * 0.25) / constants.Na
        return rho

################################################################################

class RigidRotor(Mode):
    """
    A rigid rotor approximation of (external) rotational modes. The `linear`
    attribute is :data:`True` if the associated molecule is linear, and
    :data:`False` if nonlinear. For a linear molecule, `inertia` stores a
    list with one moment of inertia in kg*m^2. For a nonlinear molecule,
    `frequencies` stores a list of the three moments of inertia, even if two or
    three are equal, in kg*m^2. The symmetry number of the rotation is stored
    in the `symmetry` attribute.
    """

    def __init__(self, linear=False, inertia=None, symmetry=1):
        self.linear = linear
        self.inertia = inertia or []
        self.symmetry = symmetry

    def __repr__(self):
        """
        Return a string representation that can be used to reconstruct the
        object.
        """
        inertia = ', '.join(['%g' % i for i in self.inertia])
        return 'RigidRotor(linear=%s, inertia=[%s], symmetry=%s)' % (self.linear, inertia, self.symmetry)

    def getPartitionFunction(self, T):
        """
        Return the value of the partition function at the specified temperatures
        `Tlist` in K. The formula is

        .. math:: q_\\mathrm{rot}(T) = \\frac{8 \\pi^2 I k_\\mathrm{B} T}{\\sigma h^2}

        for linear rotors and

        .. math:: q_\\mathrm{rot}(T) = \\frac{\\sqrt{\\pi}}{\\sigma} \\left( \\frac{8 \\pi^2 k_\\mathrm{B} T}{h^2} \\right)^{3/2} \\sqrt{I_\\mathrm{A} I_\\mathrm{B} I_\\mathrm{C}}

        for nonlinear rotors. Above, :math:`T` is temperature, :math:`\\sigma`
        is the symmetry number, :math:`I` is the moment of inertia,
        :math:`k_\\mathrm{B}` is the Boltzmann constant, and :math:`h` is the
        Planck constant.
        """
        cython.declare(theta=cython.double, inertia=cython.double)
        if self.linear:
            theta = constants.h * constants.h / (8 * constants.pi * constants.pi * self.inertia[0] * constants.kB)
            return T / theta / self.symmetry
        else:
            theta = 1.0
            for inertia in self.inertia:
                theta *= constants.h * constants.h / (8 * constants.pi * constants.pi * inertia * constants.kB)
            return numpy.sqrt(constants.pi * T**len(self.inertia) / theta) / self.symmetry

    def getHeatCapacity(self, T):
        """
        Return the contribution to the heat capacity due to rigid rotation
        in J/mol*K at the specified temperatures `Tlist` in K. The formula is

        .. math:: \\frac{C_\\mathrm{v}^\\mathrm{rot}(T)}{R} = 1

        if linear and

        .. math:: \\frac{C_\\mathrm{v}^\\mathrm{rot}(T)}{R} = \\frac{3}{2}

        if nonlinear, where :math:`T` is temperature and :math:`R` is the gas
        law constant.
        """
        if self.linear:
            return constants.R
        else:
            return 1.5 * constants.R

    def getEnthalpy(self, T):
        """
        Return the contribution to the enthalpy due to rigid rotation in J/mol
        at the specified temperatures `Tlist` in K. The formula is

        .. math:: \\frac{H^\\mathrm{rot}(T)}{RT} = 1

        for linear rotors and

        .. math:: \\frac{H^\\mathrm{rot}(T)}{RT} = \\frac{3}{2}

        for nonlinear rotors, where :math:`T` is temperature and :math:`R` is
        the gas law constant.
        """
        if self.linear:
            return constants.R * T
        else:
            return 1.5 * constants.R * T

    def getEntropy(self, T):
        """
        Return the contribution to the entropy due to rigid rotation in J/mol*K
        at the specified temperatures `Tlist` in K. The formula is

        .. math:: \\frac{S^\\mathrm{rot}(T)}{R} = \\ln Q^\\mathrm{rot} + 1

        for linear rotors and

        .. math:: \\frac{S^\\mathrm{rot}(T)}{R} = \\ln Q^\\mathrm{rot} + \\frac{3}{2}

        for nonlinear rotors, where :math:`Q^\\mathrm{rot}` is the partition
        function for a rigid rotor and :math:`R` is the gas law constant.
        """
        if self.linear:
            return (numpy.log(self.getPartitionFunction(T)) + 1.0) * constants.R
        else:
            return (numpy.log(self.getPartitionFunction(T)) + 1.5) * constants.R

    def getDensityOfStates(self, Elist):
        """
        Return the density of states at the specified energlies `Elist` in J/mol
        above the ground state in mol/J. The formula is

        .. math:: \\rho(E) = \\frac{8 \\pi^2 I}{\\sigma h^2}

        for linear rotors and

        .. math:: \\rho(E) = \\frac{\\sqrt{\\pi}}{\\sigma} \\left( \\frac{8 \\pi^2}{h^2} \\right)^{3/2} \\sqrt{I_\\mathrm{A} I_\\mathrm{B} I_\\mathrm{C}} \\frac{E^{1/2}}{\\frac{1}{2}!}

        for nonlinear rotors. Above, :math:`E` is energy, :math:`\\sigma`
        is the symmetry number, :math:`I` is the moment of inertia,
        :math:`k_\\mathrm{B}` is the Boltzmann constant, and :math:`h` is the
        Planck constant.
        """
        cython.declare(theta=cython.double, inertia=cython.double)
        if self.linear:
            theta = constants.h * constants.h / (8 * constants.pi * constants.pi * self.inertia[0]) * constants.Na
            return numpy.ones_like(Elist) / theta / self.symmetry
        else:
            theta = 1.0
            for inertia in self.inertia:
                theta *= constants.h * constants.h / (8 * constants.pi * constants.pi * inertia) * constants.Na
            return 2.0 * numpy.sqrt(Elist / theta) / self.symmetry

################################################################################

class HinderedRotor(Mode):
    """
    A one-dimensional hindered rotor using one of two potential functions:
    the the cosine potential function

    .. math:: V(\\phi) = \\frac{1}{2} V_0 \\left[1 - \\cos \\left( \\sigma \\phi \\right) \\right]

    where :math:`V_0` is the height of the potential barrier and
    :math:`\\sigma` is the number of minima or maxima in one revolution of
    angle :math:`\\phi`, equivalent to the symmetry number of that rotor;
    or a Fourier series

    .. math:: V(\\phi) = A + \\sum_{k=1}^C \\left( a_k \\cos k \\phi + b_k \\sin k \\phi \\right)

    For the cosine potential, the hindered rotor is described by the `barrier`
    height in J/mol. For the Fourier series potential, the potential is instead
    defined by a :math:`C \\times 2` array `fourier` containing the Fourier
    coefficients. Both forms require the reduced moment of `inertia` of the
    rotor in kg*m^2 and the `symmetry` number.
    If both sets of parameters are available, the Fourier series will be used,
    as it is more accurate. However, it is also significantly more
    computationally demanding.
    """

    def __init__(self, inertia=0.0, barrier=0.0, symmetry=1, fourier=None):
        self.inertia = inertia
        self.barrier = barrier
        self.symmetry = symmetry
        self.fourier = fourier
        self.energies = None
        if self.fourier is not None: self.energies = self.__solveSchrodingerEquation()

    def __repr__(self):
        """
        Return a string representation that can be used to reconstruct the
        object.
        """
        return 'HinderedRotor(inertia=%g, barrier=%g, symmetry=%g, fourier=%s)' % (self.inertia, self.barrier, self.symmetry, self.fourier)

    def getPotential(self, phi):
        """
        Return the values of the hindered rotor potential :math:`V(\\phi)`
        in J/mol at the angles `phi` in radians.
        """
        cython.declare(V=numpy.ndarray, k=cython.int)
        V = numpy.zeros_like(phi)
        if self.fourier is not None:
            for k in range(self.fourier.shape[1]):
                V += self.fourier[0,k] * numpy.cos((k+1) * phi) + self.fourier[1,k] * numpy.sin((k+1) * phi)
            V -= numpy.sum(self.fourier[0,:])
        else:
            V = 0.5 * self.barrier * (1 - numpy.cos(self.symmetry * phi))
        return V

    def __solveSchrodingerEquation(self):
        """
        Solves the one-dimensional time-independent Schrodinger equation

        .. math:: -\\frac{\\hbar}{2I} \\frac{d^2 \\psi}{d \\phi^2} + V(\\phi) \\psi(\\phi) = E \\psi(\\phi)

        where :math:`I` is the reduced moment of inertia for the rotor and
        :math:`V(\\phi)` is the rotation potential function, to determine the
        energy levels of a one-dimensional hindered rotor with a Fourier series
        potential. The solution method utilizes an orthonormal basis set
        expansion of the form

        .. math:: \\psi (\\phi) = \\sum_{m=-M}^M c_m \\frac{e^{im\\phi}}{\\sqrt{2*\\pi}}

        which converts the Schrodinger equation into a standard eigenvalue
        problem. For the purposes of this function it is sufficient to set
        :math:`M = 200`, which corresponds to 401 basis functions. Returns the
        energy eigenvalues of the Hamiltonian matrix in J/mol.
        """
        cython.declare(M=cython.int, m=cython.int, row=cython.int, n=cython.int)
        cython.declare(H=numpy.ndarray, fourier=numpy.ndarray, A=cython.double, E=numpy.ndarray)
        # The number of terms to use is 2*M + 1, ranging from -m to m inclusive
        M = 200
        # Populate Hamiltonian matrix
        H = numpy.zeros((2*M+1,2*M+1), numpy.complex64)
        fourier = self.fourier / constants.Na / 2.0
        A = numpy.sum(self.fourier[0,:]) / constants.Na
        row = 0
        for m in range(-M, M+1):
            H[row,row] = A + constants.h * constants.h * m * m / (8 * math.pi * math.pi * self.inertia)
            for n in range(fourier.shape[1]):
                if row-n-1 > -1:    H[row,row-n-1] = complex(fourier[0,n], - fourier[1,n])
                if row+n+1 < 2*M+1: H[row,row+n+1] = complex(fourier[0,n], fourier[1,n])
            row += 1
        # The overlap matrix is the identity matrix, i.e. this is a standard
        # eigenvalue problem
        # Find the eigenvalues and eigenvectors of the Hamiltonian matrix
        E, V = numpy.linalg.eigh(H)
        # Return the eigenvalues
        return (E - numpy.min(E)) * constants.Na

    def getPartitionFunction(self, T):
        """
        Return the value of the partition function at the specified temperatures
        `Tlist` in K. For the cosine potential, the formula makes use of the
        Pitzer-Gwynn approximation:

        .. math:: q_\\mathrm{hind}(T) = \\frac{q_\\mathrm{vib}^\\mathrm{quant}(T)}{q_\\mathrm{vib}^\\mathrm{class}(T)} q_\\mathrm{hind}^\\mathrm{class}(T)

        Substituting in for the right-hand side partition functions gives

        .. math:: q_\\mathrm{hind}(T) = \\frac{h \\nu}{k_\\mathrm{B} T} \\frac{1}{1 - \\exp \\left(- h \\nu / k_\\mathrm{B} T \\right)} \\left( \\frac{2 \\pi I k_\\mathrm{B} T}{h^2} \\right)^{1/2} \\frac{2 \\pi}{\\sigma} \\exp \\left( -\\frac{V_0}{2 k_\\mathrm{B} T} \\right) I_0 \\left( \\frac{V_0}{2 k_\\mathrm{B} T} \\right)

        where

        .. math:: \\nu = \\frac{\\sigma}{2 \\pi} \\sqrt{\\frac{V_0}{2 I}}

        :math:`T` is temperature, :math:`V_0` is the barrier height,
        :math:`I` is the moment of inertia, :math:`\\sigma` is the symmetry
        number, :math:`k_\\mathrm{B}` is the Boltzmann constant, and :math:`h`
        is the Planck constant. :math:`I_0(x)` is the modified Bessel function
        of order zero for argument :math:`x`.

        For the Fourier series potential, we solve the corresponding 1D
        Schrodinger equation to obtain the energy levels of the rotor and
        utilize the expression

        .. math:: q_\\mathrm{hind}(T) = \\frac{1}{\\sigma} \\sum_i e^{-\\beta E_i}

        to obtain the partition function.
        """
        if self.fourier is not None:
            # Fourier series data found, so use it
            # This means solving the 1D Schrodinger equation - slow!
            cython.declare(Q=cython.double, E=numpy.ndarray, e_kT=numpy.ndarray, i=cython.int)
            e_kT = numpy.exp(-self.energies / constants.R / T)
            Q = numpy.sum(e_kT)
            return Q / self.symmetry    # No Fourier data, so use the cosine potential data
        else:
            cython.declare(frequency=cython.double, x=cython.double, z=cython.double)
            frequency = self.getFrequency() * constants.c * 100
            x = constants.h * frequency / (constants.kB * T)
            z = 0.5 * self.barrier / (constants.R * T)
            return x / (1 - numpy.exp(-x)) * numpy.sqrt(2 * math.pi * self.inertia * constants.kB * T / constants.h / constants.h) * (2 * math.pi / self.symmetry) * numpy.exp(-z) * besseli0(z)

    def getHeatCapacity(self, T):
        """
        Return the contribution to the heat capacity due to hindered rotation
        in J/mol*K at the specified temperatures `Tlist` in K.

        For the cosine potential, the formula is

        .. math:: \\frac{C_\\mathrm{v}^\\mathrm{hind}(T)}{R} = \\frac{C_\\mathrm{v}^\\mathrm{vib}(T)}{R} -\\frac{1}{2} + \\zeta^2 - \\left[ \\zeta \\frac{I_1(\\zeta)}{I_0(\\zeta)} \\right]^2 - \\zeta \\frac{I_1(\\zeta)}{I_0(\\zeta)}

        where :math:`\\zeta \\equiv V_0 / 2 k_\\mathrm{B} T`,
        :math:`T` is temperature, :math:`V_0` is the barrier height,
        :math:`k_\\mathrm{B}` is the Boltzmann constant, and :math:`R` is the
        gas law constant.

        For the Fourier series potential, we solve the corresponding 1D
        Schrodinger equation to obtain the energy levels of the rotor and
        utilize the expression

        .. math:: \\frac{C_\\mathrm{v}^\\mathrm{hind}(T)}{R} = \\beta^2 \\frac{\\left( \\sum_i E_i^2 e^{-\\beta E_i} \\right) \\left( \\sum_i e^{-\\beta E_i} \\right) - \\left( \\sum_i E_i e^{-\\beta E_i} \\right)^2}{\\left( \\sum_i e^{-\\beta E_i} \\right)^2}

        to obtain the heat capacity.
        """
        if self.fourier is not None:
            cython.declare(Cv=cython.double, E=numpy.ndarray, e_kT=numpy.ndarray, i=cython.int)
            E = self.energies
            e_kT = numpy.exp(-E / constants.R / T)
            Cv = (numpy.sum(E*E*e_kT) * numpy.sum(e_kT) - numpy.sum(E*e_kT)**2) / (constants.R*T*T * numpy.sum(e_kT)**2)
            return Cv
        else:
            cython.declare(frequency=cython.double, x=cython.double, z=cython.double)
            cython.declare(exp_x=cython.double, one_minus_exp_x=cython.double, BB=cython.double)
            frequency = self.getFrequency() * constants.c * 100
            x = constants.h * frequency / (constants.kB * T)
            z = 0.5 * self.barrier / (constants.R * T)
            exp_x = numpy.exp(x)
            one_minus_exp_x = 1.0 - exp_x
            BB = besseli1(z) / besseli0(z)
            return (x * x * exp_x / one_minus_exp_x / one_minus_exp_x - 0.5 + z * (z - BB - z * BB * BB)) * constants.R

    def getEnthalpy(self, T):
        """
        Return the contribution to the heat capacity due to hindered rotation
        in J/mol at the specified temperatures `Tlist` in K. For the cosine
        potential, this is calculated numerically from the partition function.
        For the Fourier series potential, we solve the corresponding 1D
        Schrodinger equation to obtain the energy levels of the rotor and
        utilize the expression

        .. math:: H^\\mathrm{hind}(T) - H_0 = \\frac{\\sum_i E_i e^{-\\beta E_i}}{\\sum_i e^{-\\beta E_i}}

        to obtain the enthalpy.
        """
        if self.fourier is not None:
            cython.declare(H=cython.double, E=numpy.ndarray, e_kT=numpy.ndarray, i=cython.int)
            E = self.energies
            e_kT = numpy.exp(-E / constants.R / T)
            H = numpy.sum(E*e_kT) / numpy.sum(e_kT)
            return H
        else:
            Tlow = T * 0.999
            Thigh = T * 1.001
            return (T *
                (numpy.log(self.getPartitionFunction(Thigh)) -
                numpy.log(self.getPartitionFunction(Tlow))) /
                (Thigh - Tlow)) * constants.R * T

    def getEntropy(self, T):
        """
        Return the contribution to the heat capacity due to hindered rotation
        in J/mol*K at the specified temperatures `Tlist` in K. For the cosine
        potential, this is calculated numerically from the partition function.
        For the Fourier series potential, we solve the corresponding 1D
        Schrodinger equation to obtain the energy levels of the rotor and
        utilize the expression

        .. math:: S^\\mathrm{hind}(T) = R \\left( \\ln q_\\mathrm{hind}(T) + \\frac{\\sum_i E_i e^{-\\beta E_i}}{RT \\sum_i e^{-\\beta E_i}} \\right)

        to obtain the entropy.
        """
        if self.fourier is not None:
            cython.declare(S=cython.double, E=numpy.ndarray, e_kT=numpy.ndarray, i=cython.int)
            E = self.energies
            S = constants.R * numpy.log(self.getPartitionFunction(T))
            e_kT = numpy.exp(-E / constants.R / T)
            S += numpy.sum(E*e_kT) / (T * numpy.sum(e_kT))
            return S
        else:
            Tlow = T * 0.999
            Thigh = T * 1.001
            return (numpy.log(self.getPartitionFunction(Thigh)) +
                T * (numpy.log(self.getPartitionFunction(Thigh)) -
                numpy.log(self.getPartitionFunction(Tlow))) /
                (Thigh - Tlow)) * constants.R

    def getDensityOfStates(self, Elist):
        """
        Return the density of states at the specified energlies `Elist` in J/mol
        above the ground state. For the cosine potential, the formula is

        .. math:: \\rho(E) = \\frac{2 q_\\mathrm{1f}}{\\pi^{3/2} V_0^{1/2}} \\mathcal{K}(E / V_0) \\hspace{20pt} E < V_0

        and

        .. math:: \\rho(E) = \\frac{2 q_\\mathrm{1f}}{\\pi^{3/2} E^{1/2}} \\mathcal{K}(V_0 / E) \\hspace{20pt} E > V_0

        where

        .. math:: q_\\mathrm{1f} = \\frac{\\pi^{1/2}}{\\sigma} \\left( \\frac{8 \\pi^2 I}{h^2} \\right)^{1/2}

        :math:`E` is energy, :math:`V_0` is barrier height, and
        :math:`\\mathcal{K}(x)` is the complete elliptic integral of the first
        kind. There is currently no functionality for using the Fourier series
        potential.
        """
        cython.declare(rho=numpy.ndarray, q1f=cython.double, pre=cython.double, V0=cython.double, i=cython.int)
        rho = numpy.zeros_like(Elist)
        q1f = math.sqrt(8 * math.pi * math.pi * math.pi * self.inertia / constants.h / constants.h / constants.Na) / self.symmetry
        V0 = self.barrier
        pre = 2.0 * q1f / math.sqrt(math.pi * math.pi * math.pi * V0)
        # The following is only valid in the classical limit
        # Note that cellipk(1) = infinity, so we must skip that value
        for i in range(len(Elist)):
            if Elist[i] / V0 < 1:
                rho[i] = pre * cellipk(Elist[i] / V0)
            elif Elist[i] / V0 > 1:
                rho[i] = pre * math.sqrt(V0 / Elist[i]) * cellipk(V0 / Elist[i])
        return rho

    def getFrequency(self):
        """
        Return the frequency of vibration corresponding to the limit of
        harmonic oscillation. The formula is

        .. math:: \\nu = \\frac{\\sigma}{2 \\pi} \\sqrt{\\frac{V_0}{2 I}}

        where :math:`\\sigma` is the symmetry number, :math:`V_0` the barrier
        height, and :math:`I` the reduced moment of inertia of the rotor. The
        units of the returned frequency are cm^-1.
        """
        V0 = self.barrier
        if self.fourier is not None:
            V0 = -numpy.sum(self.fourier[:,0])
        return self.symmetry / 2.0 / math.pi * math.sqrt(V0 / constants.Na / 2 / self.inertia) / (constants.c * 100)

def besseli0(x):
    """
    Return the value of the zeroth-order modified Bessel function at `x`.
    """
    import scipy.special
    return scipy.special.i0(x)

def besseli1(x):
    """
    Return the value of the first-order modified Bessel function at `x`.
    """
    import scipy.special
    return scipy.special.i1(x)

def cellipk(x):
    """
    Return the value of the complete elliptic integral of the first kind at `x`.
    """
    import scipy.special
    return scipy.special.ellipk(x)

################################################################################

class HarmonicOscillator(Mode):
    """
    A representation of a set of vibrational modes as one-dimensional quantum
    harmonic oscillator. The oscillators are defined by their `frequencies` in
    cm^-1.
    """

    def __init__(self, frequencies=None):
        self.frequencies = frequencies or []

    def __repr__(self):
        """
        Return a string representation that can be used to reconstruct the
        object.
        """
        frequencies = ', '.join(['%g' % freq for freq in self.frequencies])
        return 'HarmonicOscillator(frequencies=[%s])' % (frequencies)

    def getPartitionFunction(self, T):
        """
        Return the value of the partition function at the specified temperatures
        `Tlist` in K. The formula is

        .. math:: q_\\mathrm{vib}(T) = \\prod_i \\frac{1}{1 - e^{-\\xi_i}}

        where :math:`\\xi_i \\equiv h \\nu_i / k_\\mathrm{B} T`,
        :math:`T` is temperature, :math:`\\nu_i` is the frequency of vibration
        :math:`i`, :math:`k_\\mathrm{B}` is the Boltzmann constant, :math:`h`
        is the Planck constant, and :math:`R` is the gas law constant. Note
        that we have chosen our zero of energy to be at the zero-point energy
        of the molecule, *not* the bottom of the potential well.
        """
        cython.declare(Q=cython.double, freq=cython.double)
        Q = 1.0
        for freq in self.frequencies:
            Q = Q / (1 - numpy.exp(-freq / (0.695039 * T)))  # kB = 0.695039 cm^-1/K
        return Q

    def getHeatCapacity(self, T):
        """
        Return the contribution to the heat capacity due to vibration
        in J/mol*K at the specified temperatures `Tlist` in K. The formula is

        .. math:: \\frac{C_\\mathrm{v}^\\mathrm{vib}(T)}{R} = \\sum_i \\xi_i^2 \\frac{e^{\\xi_i}}{\\left( 1 - e^{\\xi_i} \\right)^2}

        where :math:`\\xi_i \\equiv h \\nu_i / k_\\mathrm{B} T`,
        :math:`T` is temperature, :math:`\\nu_i` is the frequency of vibration
        :math:`i`, :math:`k_\\mathrm{B}` is the Boltzmann constant, :math:`h`
        is the Planck constant, and :math:`R` is the gas law constant.
        """
        cython.declare(Cv=cython.double, freq=cython.double)
        cython.declare(x=cython.double, exp_x=cython.double, one_minus_exp_x=cython.double)
        Cv = 0.0
        for freq in self.frequencies:
            x = freq / (0.695039 * T)	# kB = 0.695039 cm^-1/K
            exp_x = numpy.exp(x)
            one_minus_exp_x = 1.0 - exp_x
            Cv = Cv + x * x * exp_x / one_minus_exp_x / one_minus_exp_x
        return Cv * constants.R

    def getEnthalpy(self, T):
        """
        Return the contribution to the enthalpy due to vibration in J/mol at
        the specified temperatures `Tlist` in K. The formula is

        .. math:: \\frac{H^\\mathrm{vib}(T)}{RT} = \\sum_i \\frac{\\xi_i}{e^{\\xi_i} - 1}

        where :math:`\\xi_i \\equiv h \\nu_i / k_\\mathrm{B} T`,
        :math:`T` is temperature, :math:`\\nu_i` is the frequency of vibration
        :math:`i`, :math:`k_\\mathrm{B}` is the Boltzmann constant, :math:`h`
        is the Planck constant, and :math:`R` is the gas law constant.
        """
        cython.declare(H=cython.double, freq=cython.double)
        cython.declare(x=cython.double, exp_x=cython.double)
        H = 0.0
        for freq in self.frequencies:
            x = freq / (0.695039 * T)	# kB = 0.695039 cm^-1/K
            exp_x = numpy.exp(x)
            H = H + x / (exp_x - 1)
        return H * constants.R * T

    def getEntropy(self, T):
        """
        Return the contribution to the entropy due to vibration in J/mol*K at
        the specified temperatures `Tlist` in K. The formula is

        .. math:: \\frac{S^\\mathrm{vib}(T)}{R} = \\sum_i \\left[ - \\ln \\left(1 - e^{-\\xi_i} \\right) + \\frac{\\xi_i}{e^{\\xi_i} - 1} \\right]

        where :math:`\\xi_i \\equiv h \\nu_i / k_\\mathrm{B} T`,
        :math:`T` is temperature, :math:`\\nu_i` is the frequency of vibration
        :math:`i`, :math:`k_\\mathrm{B}` is the Boltzmann constant, :math:`h`
        is the Planck constant, and :math:`R` is the gas law constant.
        """
        cython.declare(S=cython.double, freq=cython.double)
        cython.declare(x=cython.double, exp_x=cython.double)
        S = numpy.log(self.getPartitionFunction(T))
        for freq in self.frequencies:
            x = freq / (0.695039 * T)	# kB = 0.695039 cm^-1/K
            exp_x = numpy.exp(x)
            S = S + x / (exp_x - 1)
        return S * constants.R

    def getDensityOfStates(self, Elist, rho0=None):
        """
        Return the density of states at the specified energies `Elist` in J/mol
        above the ground state. The Beyer-Swinehart method is used to
        efficiently convolve the vibrational density of states into the
        density of states of other modes. To be accurate, this requires a small
        (:math:`1-10 \\ \\mathrm{cm^{-1}}` or so) energy spacing.
        """
        cython.declare(rho=numpy.ndarray, freq=cython.double)
        cython.declare(dE=cython.double, nE=cython.int, dn=cython.int, n=cython.int)
        if rho0 is not None:
            rho = rho0
        else:
            rho = numpy.zeros_like(Elist)
        dE = Elist[1] - Elist[0]
        nE = len(Elist)
        for freq in self.frequencies:
            dn = int(freq * constants.h * constants.c * 100 * constants.Na / dE)
            for n in range(dn+1, nE):
                rho[n] = rho[n] + rho[n-dn]
        return rho

################################################################################

class StatesModel:
    """
    A set of molecular degrees of freedom data for a given molecule, comprising
    the results of a quantum chemistry calculation.

    =================== =================== ====================================
    Attribute           Type                Description
    =================== =================== ====================================
    `modes`             ``list``            A list of the degrees of freedom
    `spinMultiplicity`  ``int``             The spin multiplicity of the molecule
    =================== =================== ====================================

    """

    def __init__(self, modes=None, spinMultiplicity=1):
        self.modes = modes or []
        self.spinMultiplicity = spinMultiplicity

    def getHeatCapacity(self, T):
        """
        Return the constant-pressure heat capacity in J/mol*K at the specified
        temperatures `Tlist` in K.
        """
        cython.declare(Cp=cython.double)
        Cp = constants.R
        for mode in self.modes:
            Cp += mode.getHeatCapacity(T)
        return Cp

    def getEnthalpy(self, T):
        """
        Return the enthalpy in J/mol at the specified temperatures `Tlist` in K.
        """
        cython.declare(H=cython.double)
        H = constants.R * T
        for mode in self.modes:
            H += mode.getEnthalpy(T)
        return H

    def getEntropy(self, T):
        """
        Return the entropy in J/mol*K at the specified temperatures `Tlist` in
        K.
        """
        cython.declare(S=cython.double)
        S = 0.0
        for mode in self.modes:
            S += mode.getEntropy(T)
        return S

    def getPartitionFunction(self, T):
        """
        Return the the partition function at the specified temperatures
        `Tlist` in K. An active K-rotor is automatically included if there are
        no external rotational modes.
        """
        cython.declare(Q=cython.double, Trot=cython.double)
        Q = 1.0
        # Active K-rotor
        rotors = [mode for mode in self.modes if isinstance(mode, RigidRotor)]
        if len(rotors) == 0:
            Trot = 1.0 / constants.R / 3.141592654
            Q *= numpy.sqrt(T / Trot)
        # Other modes
        for mode in self.modes:
            Q *= mode.getPartitionFunction(T)
        return Q * self.spinMultiplicity

    def getDensityOfStates(self, Elist):
        """
        Return the value of the density of states in mol/J at the specified
        energies `Elist` in J/mol above the ground state. An active K-rotor is
        automatically included if there are no external rotational modes.
        """
        cython.declare(rho=numpy.ndarray, i=cython.int, E=cython.double)
        rho = numpy.zeros_like(Elist)
        # Active K-rotor
        rotors = [mode for mode in self.modes if isinstance(mode, RigidRotor)]
        if len(rotors) == 0:
            rho0 = numpy.zeros_like(Elist)
            for i, E in enumerate(Elist):
                if E > 0: rho0[i] = 1.0 / math.sqrt(1.0 * E)
            rho = convolve(rho, rho0, Elist)
        # Other non-vibrational modes
        for mode in self.modes:
            if not isinstance(mode, HarmonicOscillator):
                rho = convolve(rho, mode.getDensityOfStates(Elist), Elist)
        # Vibrational modes
        for mode in self.modes:
            if isinstance(mode, HarmonicOscillator):
                rho = mode.getDensityOfStates(Elist, rho)
        return rho * self.spinMultiplicity

    def getSumOfStates(self, Elist):
        """
        Return the value of the sum of states at the specified energies `Elist`
        in J/mol above the ground state. The sum of states is computed via
        numerical integration of the density of states.
        """
        cython.declare(densStates=numpy.ndarray, sumStates=numpy.ndarray, i=cython.int, dE=cython.double)
        densStates = self.getDensityOfStates(Elist)
        sumStates = numpy.zeros_like(densStates)
        dE = Elist[1] - Elist[0]
        for i in range(len(densStates)):
            sumStates[i] = numpy.sum(densStates[0:i]) * dE
        return sumStates
    
    def getPartitionFunctions(self, Tlist):
        return numpy.array([self.getPartitionFunction(T) for T in Tlist], numpy.float64)

    def getHeatCapacities(self, Tlist):
        return numpy.array([self.getHeatCapacity(T) for T in Tlist], numpy.float64)

    def getEnthalpies(self, Tlist):
        return numpy.array([self.getEnthalpy(T) for T in Tlist], numpy.float64)

    def getEntropies(self, Tlist):
        return numpy.array([self.getEntropy(T) for T in Tlist], numpy.float64)

    def __phi(self, beta, E):
        beta = float(beta)
        cython.declare(T=numpy.ndarray, Q=cython.double)
        Q = self.getPartitionFunction(1.0 / (constants.R * beta))
        return math.log(Q) + beta * float(E)

    def getDensityOfStatesILT(self, Elist, order=1):
        """
        Return the value of the density of states in mol/J at the specified
        energies `Elist` in J/mol above the ground state, calculated by
        numerical inverse Laplace transform of the partition function using
        the method of steepest descents. This method is generally slower than
        direct density of states calculation, but is guaranteed to correspond
        with the partition function. The optional `order` attribute controls
        the order of the steepest descents approximation applied (1 = first,
        2 = second); the first-order approximation is slightly less accurate,
        smoother, and faster to calculate than the second-order approximation.
        This method is adapted from the discussion in Forst [Forst2003]_.

        .. [Forst2003] W. Forst.
            *Unimolecular Reactions: A Concise Introduction.*
            Cambridge University Press (2003).
            `isbn:978-0-52-152922-8 <http://www.cambridge.org/9780521529228>`_

        """
        import scipy.optimize
        cython.declare(rho=numpy.ndarray)
        cython.declare(x=cython.double, E=cython.double, dx=cython.double, f=cython.double)
        cython.declare(d2fdx2=cython.double, d3fdx3=cython.double, d4fdx4=cython.double)
        rho = numpy.zeros_like(Elist)
        # Initial guess for first minimization
        x = 1e-5
        # Iterate over energies
        for i in range(1, len(Elist)):
            E = Elist[i]
            # Find minimum of phi         func x0 arg  xtol  ftol maxi  maxf fullout  disp retall  callback
            x = scipy.optimize.fmin(self.__phi, x, [Elist[i]], 1e-8, 1e-8, 100, 1000, False, False, False, None)
            x = float(x)
            dx = 1e-4 * x
            # Determine value of density of states using steepest descents approximation
            d2fdx2 = (self.__phi(x+dx, E) - 2 * self.__phi(x, E) + self.__phi(x-dx, E)) / (dx**2)
            # Apply first-order steepest descents approximation (accurate to 1-3%, smoother)
            f = self.__phi(x, E)
            rho[i] = math.exp(f) / math.sqrt(2 * math.pi * d2fdx2)
            if order == 2:
                # Apply second-order steepest descents approximation (more accurate, less smooth)
                d3fdx3 = (self.__phi(x+1.5*dx, E) - 3 * self.__phi(x+0.5*dx, E) + 3 * self.__phi(x-0.5*dx, E) - self.__phi(x-1.5*dx, E)) / (dx**3)
                d4fdx4 = (self.__phi(x+2*dx, E) - 4 * self.__phi(x+dx, E) + 6 * self.__phi(x, E) - 4 * self.__phi(x-dx, E) + self.__phi(x-2*dx, E)) / (dx**4)
                rho[i] *= 1 + d4fdx4 / 8 / (d2fdx2**2) - 5 * (d3fdx3**2) / 24 / (d2fdx2**3)
        return rho

def convolve(rho1, rho2, Elist):
    """
    Convolutes two density of states arrays `rho1` and `rho2` with corresponding
    energies `Elist` together using the equation

    .. math:: \\rho(E) = \\int_0^E \\rho_1(x) \\rho_2(E-x) \\, dx

    The units of the parameters do not matter so long as they are consistent.
    """

    cython.declare(rho=numpy.ndarray, found1=cython.bint, found2=cython.bint)
    cython.declare(dE=cython.double, nE=cython.int, i=cython.int, j=cython.int)
    rho = numpy.zeros_like(Elist)

    found1 = rho1.any(); found2 = rho2.any()
    if not found1 and not found2:
        pass
    elif found1 and not found2:
        rho = rho1
    elif not found1 and found2:
        rho = rho2
    else:
        dE = Elist[1] - Elist[0]
        nE = len(Elist)
        for i in range(nE):
            for j in range(i+1):
                rho[i] += rho2[i-j] * rho1[i] * dE

    return rho
