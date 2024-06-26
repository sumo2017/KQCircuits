# This code is part of KQCircuits
# Copyright (C) 2024 IQM Finland Oy
#
# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with this program. If not, see
# https://www.gnu.org/licenses/gpl-3.0.html.
#
# The software distribution should follow IQM trademark policy for open-source software
# (meetiqm.com/developers/osstmpolicy). IQM welcomes contributions to the code. Please see our contribution agreements
# for individuals (meetiqm.com/developers/clas/individual) and organizations (meetiqm.com/developers/clas/organization).
from dataclasses import dataclass, field
from typing import Union, List, ClassVar
from kqcircuits.simulations.export.solution import Solution


@dataclass
class ElmerSolution(Solution):
    """
    A Base class for Elmer Solution parameters

    Args:
        p_element_order: polynomial order of p-elements
        percent_error: Stopping criterion in adaptive meshing.
        max_error_scale: Maximum element error, relative to percent_error, allowed in individual elements.
        max_outlier_fraction: Maximum fraction of outliers from the total number of elements
        maximum_passes: Maximum number of adaptive meshing iterations.
        minimum_passes: Minimum number of adaptive meshing iterations.
        is_axisymmetric: Simulate with Axi Symmetric coordinates along :math:`y\\Big|_{x=0}` (Default: False)
        mesh_levels: If set larger than 1 Elmer will make the mesh finer by dividing each element
                     into 2^(dim) elements mesh_levels times. Default 1.
        mesh_size: Dictionary to determine mesh size where key (string) denotes material and value (double) denotes the
            maximal length of mesh element. Additional mesh size terms can be determined, if the value type is
            list. Then, term[0] is the maximal mesh element length inside at the entity and its expansion,
            term[1] is expansion distance in which the maximal mesh element length is constant (default=term[0]),
            and term[2] is the slope of the increase in the maximal mesh element length outside the entity.
            To refine material interface the material names by should be separated by '&' in the key. Key 'global_max'
            is reserved for setting global maximal element length. For example, if the dictionary is given as
            {'substrate': 10, 'substrate&vacuum': [2, 5], 'global_max': 100}, then the maximal mesh element length is 10
            inside the substrate and 2 on region which is less than 5 units away from the substrate-vacuum interface.
            Outside these regions, the mesh element size can increase up to 100.

    """

    tool: ClassVar[str] = ""

    p_element_order: int = 3
    percent_error: float = 0.005
    max_error_scale: float = 2.0
    max_outlier_fraction: float = 1e-3
    maximum_passes: int = 1
    minimum_passes: int = 1
    is_axisymmetric: bool = False
    mesh_levels: int = 1
    mesh_size: dict = field(default_factory=dict)

    def get_solution_data(self):
        """Return the solution data in dictionary form."""
        sol_dict = {**self.__dict__, "tool": self.tool}
        sol_dict["solution_name"] = sol_dict.pop("name")
        return sol_dict


@dataclass
class ElmerVectorHelmholtzSolution(ElmerSolution):
    """
    Class for Elmer wave-equation solution parameters

    Args:
        frequency: Units are in GHz. Give a list of frequencies if using interpolating sweep.
        frequency_batch: Number of frequencies calculated between each round of fitting in interpolating sweep
        sweep_type: Type of frequency sweep. Options "explicit" and "interpolating".
        max_delta_s: Convergence tolerance in interpolating sweep
        london_penetration_depth: Allows supercurrent to flow on the metal boundaries within a layer
                                  of thickness `london_penetration_depth`
        quadratic_approximation: Use edge finite elements of second degree
        second_kind_basis: Use Nedelec finite elements of second kind

        use_av: Use a formulation of VectorHelmHoltz equation based on potentials A-V instead of electric field E.
                For details see https://www.nic.funet.fi/pub/sci/physics/elmer/doc/ElmerModelsManual.pdf
                WARNING: This option is experimental and might lead to poor convergence.
        conductivity: Adds a specified film conductivity on metal boundaries. Applies only when `use_av=True`
        nested_iteration: Enables alternative nested iterative solver to be used. Applies only when `use_av=True`
        convergence_tolerance: Convergence tolerance of the iterative solver. Applies only when `use_av=True`
        max_iterations: Maximum number of iterations for the iterative solver. Applies only when `use_av=True`
    """

    tool: ClassVar[str] = "wave_equation"

    frequency: Union[float, List[float]] = 5
    frequency_batch: int = 3
    sweep_type: str = "explicit"
    max_delta_s: float = 0.01
    london_penetration_depth: float = 0
    quadratic_approximation: bool = False  # TODO generalize to other solvers
    second_kind_basis: bool = False  # TODO generalize to other solvers

    use_av: bool = False
    conductivity: float = 0
    nested_iteration: bool = False
    convergence_tolerance: float = 1.0e-10  # TODO generalize to other solvers
    max_iterations: int = 2000  # TODO generalize to other solvers

    def __post_init__(self):
        """Cast frequency to list. Automatically called after init"""
        if isinstance(self.frequency, (float, int)):
            self.frequency = [self.frequency]
        elif not isinstance(self.frequency, list):
            self.frequency = list(self.frequency)


@dataclass
class ElmerCapacitanceSolution(ElmerSolution):
    """
    Class for Elmer capacitance solution parameters

    Args:
        linear_system_method: Available: 'bicgstab', 'mg' TODO Generalise to other tools
        integrate_energies: Calculate energy integrals over each object. Used in EPR simulations
    """

    tool: ClassVar[str] = "capacitance"

    linear_system_method: str = "bicgstab"
    integrate_energies: bool = False


@dataclass
class ElmerCrossSectionSolution(ElmerSolution):
    """
    Class for Elmer cross-section solution parameters

    Args:
        linear_system_method: Available: 'bicgstab', 'mg'
        integrate_energies: Calculate energy integrals over each object. Used in EPR simulations
        boundary_conditions: Parameters to determine boundary conditions for potentil on the edges
                             of simulation box. Supported keys are `xmin` , `xmax` ,`ymin` and `ymax`
                             Example: `boundary_conditions = {"xmin": {"potential": 0}}`
    """

    tool: ClassVar[str] = "cross-section"

    linear_system_method: str = "bicgstab"
    integrate_energies: bool = False
    boundary_conditions: dict = field(default_factory=dict)


def get_elmer_solution(tool="capacitance", **solution_params):
    """Returns an instance of ElmerSolution subclass.

    Args:
        tool: Determines the subclass of ElmerSolution.
        solution_params: Arguments passed for  ElmerSolution subclass.
    """
    for c in [ElmerVectorHelmholtzSolution, ElmerCapacitanceSolution, ElmerCrossSectionSolution]:
        if tool == c.tool:
            return c(**solution_params)
    raise ValueError(f"No ElmerSolution found for tool={tool}.")
