import torch
from torch import nn
import numpy
from .. import bisection_n_newton as bn
from .. import layer_base
from . import euclidean_base

import math
import torch.nn.functional as F
import torch.distributions as tdist


normal_dist=tdist.Normal(0, 1)

class euclidean_do_nothing(euclidean_base.euclidean_base):
    def __init__(self, dimension, use_permanent_parameters=True, add_offset=0):
        """
        Identitiy transformation. Symbol "x"
        """

        super().__init__(dimension=dimension, use_permanent_parameters=use_permanent_parameters, model_offset=add_offset)

    def _flow_mapping(self, inputs, extra_inputs=None): 
        
        [z, log_det]=inputs

        return z, log_det

    def _inv_flow_mapping(self, inputs, extra_inputs=None):
        
        [x, log_det] = inputs

        return x, log_det#, cur_datapoints_update
        

    def _init_params(self, params):

        assert(len(params)==0)

    def _get_desired_init_parameters(self):
        
        return torch.Tensor([])

    def _obtain_layer_param_structure(self, param_dict, extra_inputs=None, previous_x=None, extra_prefix=""): 
        """ 
        Do nothing
        """
     
        return
