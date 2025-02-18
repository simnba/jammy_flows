import torch
from torch import nn
import collections
import numpy

from . import simplex_base

from ...main import default

import torch.distributions as tdist

normal_dist=tdist.Normal(0, 1)

class inner_loop_simplex(simplex_base.simplex_base):
    def __init__(self, 
                 dimension, 
                 use_permanent_parameters=False,
                 always_parametrize_in_embedding_space=0,
                 project_from_gauss_to_simplex=0,
                 num_basis_functions=10,
                 num_inner_flow_layers=2,
                 amortization_mlp_dims="128",
                 verbose=True):
        print("version: SIMON.2")
        """
        Iterative simplex flow. Symbol: "w"

        Construction suggested in https://arxiv.org/abs/2008.05456.
        """
        super().__init__(dimension=dimension, 
                         use_permanent_parameters=use_permanent_parameters,
                         always_parametrize_in_embedding_space=always_parametrize_in_embedding_space,
                         project_from_gauss_to_simplex=project_from_gauss_to_simplex)


        flow_dict=dict()
        flow_dict["r"] = dict()
        flow_dict["r"]["num_basis_functions"]=num_basis_functions
      
        
        self.inner_flow=default.pdf("+".join(["i1_0.0_1.0"]*self.dimension),
                                  "+".join(["r"*num_inner_flow_layers]*self.dimension), 
                                  options_overwrite=flow_dict,
                                  amortize_everything=True,
                                  amortization_mlp_use_custom_mode=True, 
                                  use_as_passthrough_instead_of_pdf=True,
                                  amortization_mlp_dims=amortization_mlp_dims,
                                  verbose=verbose)
     
        #print("debug total_number_amortizable_params=", self.inner_flow.total_number_amortizable_params)
        self.total_num_inner_flow_params=self.inner_flow.total_number_amortizable_params
        self.total_param_num=self.total_num_inner_flow_params

        if(use_permanent_parameters):
            self.inner_flow_params = nn.Parameter(torch.randn(1, self.total_num_inner_flow_params))
    

    def _inv_flow_mapping(self, inputs, extra_inputs=None):

        """
        From target to base. We only transform the d-dimensional simplex coordinates, not the last d+1 th embedding cooridnate. It is used
        however in the logdet calculation to correctly calculate the PDF on the simplex manifold.
        """

        [res, log_det]=inputs

        if(extra_inputs is None):
            amortization_params=self.inner_flow_params.to(res)
        else:
            amortization_params=extra_inputs

        if(self.always_parametrize_in_embedding_space):
            # canonical to base simplex if necessary
            res, log_det=self.canonical_simplex_to_base_simplex([res, log_det])

        # base simplex to skewed box
        res, log_det=self.base_simplex_to_non_uniform_box([res, log_det])

        res,log_det=self.inner_flow.all_layer_inverse(res, log_det, None, amortization_parameters=amortization_params)
       
        res, log_det=self.non_uniform_box_to_base_simplex([res, log_det])

        if(self.always_parametrize_in_embedding_space):
            res, log_det=self.base_simplex_to_canonical_simplex([res, log_det])

        return res, log_det

    def _flow_mapping(self, inputs, extra_inputs=None):
        """
        From base to target
        """

        [res, log_det]=inputs
        if(extra_inputs is None):
            amortization_params=self.inner_flow_params.to(res)
        else:
            amortization_params=extra_inputs

        if(self.always_parametrize_in_embedding_space):
            # canonical to base simplex if necessary
            res, log_det=self.canonical_simplex_to_base_simplex([res, log_det])

        # base simplex to skewed box
        res, log_det=self.base_simplex_to_non_uniform_box([res, log_det])

        res,log_det=self.inner_flow.all_layer_forward(res, log_det, None, amortization_parameters=amortization_params)

        res, log_det=self.non_uniform_box_to_base_simplex([res, log_det])

        if(self.always_parametrize_in_embedding_space):
            res, log_det=self.base_simplex_to_canonical_simplex([res, log_det])

        return res, log_det


    def _init_params(self, params):
        """
        This function is only called if *use_permanent_parameters* is set to true.
        """
        self.inner_flow_params.data=params.reshape(1, self.total_num_inner_flow_params)
    

    #############################################################################

    #def _init_params(self, params):

        
    def _get_desired_init_parameters(self):
        
        init_params=self.inner_flow.init_params()
        
        #init_params=torch.randn(self.total_num_inner_flow_params, dtype=torch.float64)
        return init_params
        #return torch.cat(desired_param_vec)

   


    