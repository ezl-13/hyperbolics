import torch
from torch import nn
from torch.autograd import Variable
import logging
import numpy as np, math
import random

def dot(x,y): return torch.sum(x * y, -1)
def acosh(x):
    return torch.log(x + torch.sqrt(x**2-1))


class RParameter(nn.Parameter):
    def __new__(cls, data=None, requires_grad=True, sizes=None, exp=False):
        if data is None:
            assert sizes is not None
            data = (1e-3 * torch.randn(sizes, dtype=torch.double)).clamp_(min=-3e-3,max=3e-3)
        #TODO get partial data if too big i.e. data[0:n,0:d]
        ret =  super().__new__(cls, data, requires_grad=requires_grad)
        # ret.data    = data
        ret.initial_proj()
        ret.use_exp = exp
        return ret

    @staticmethod
    def _proj(x):
        raise NotImplemented

    def proj(self):
        self.data = self.__class__._proj(self.data.detach())
        # print(torch.norm(self.data, dim=-1))

    def initial_proj(self):
        """ Project the initialization of the embedding onto the manifold """
        self.proj()

    def modify_grad_inplace(self):
        pass

    @staticmethod
    def correct_metric(ps):
        for p in ps:
            if isinstance(p,RParameter):
                p.modify_grad_inplace()


# TODO can use kwargs instead of pasting defaults
class HyperboloidParameter(RParameter):
    def __new__(cls, data=None, requires_grad=True, sizes=None, exp=True):
        if sizes is not None:
            sizes = list(sizes)
            sizes[-1] += 1
        return super().__new__(cls, data, requires_grad, sizes, exp)

    @staticmethod
    def dot_h(x,y):
        return torch.sum(x * y, -1) - 2*x[...,0]*y[...,0]
    @staticmethod
    def norm_h(x):
        assert torch.all(HyperboloidParameter.dot_h(x,x) >= 0), torch.min(HyperboloidParameter.dot_h(x,x))
        return torch.sqrt(torch.clamp(HyperboloidParameter.dot_h(x,x), min=0.0))
    @staticmethod
    def dist_h(x,y):
        # print("before", x, y)
        # print("before dots", HyperboloidParameter.dot_h(x,x)+1, HyperboloidParameter.dot_h(y,y)+1)
        # print("after dots", -HyperboloidParameter.dot_h(x,y))
        # return acosh(-HyperboloidParameter.dot_h(x,y) - 1e-7)
        bad = torch.min(-HyperboloidParameter.dot_h(x,y) - 1.0)
        if bad <= -1e-4:
            print("bad dist", bad.item())
        # assert torch.all(-HyperboloidParameter.dot_h(x,y) >= 1.0 - 1e-4), torch.min(-HyperboloidParameter.dot_h(x,y) - 1.0)
	    # we're dividing by dist_h somewhere so we can't have it be 0, force dp > 1
        return acosh(torch.clamp(-HyperboloidParameter.dot_h(x,y), min=(1.0+1e-8)))

    @staticmethod
    def _proj(x):
        """ Project onto hyperboloid """
        x_ = torch.tensor(x)
        x_tail = x_[...,1:]
        current_norms = torch.norm(x_tail,2,-1)
        scale      = (current_norms/1e7).clamp_(min=1.0)
        x_tail /= scale.unsqueeze(-1)
        x_[...,1:] = x_tail
        x_[...,0] = torch.sqrt(1 + torch.norm(x_tail,2,-1)**2)

        xxx = x_ / torch.sqrt(torch.clamp(-HyperboloidParameter.dot_h(x_,x_), min=0.0)).unsqueeze(-1)
        return xxx

    def initial_proj(self):
        """ Project the initialization of the embedding onto the manifold """
        self.data[...,0] = torch.sqrt(1 + torch.norm(self.data.detach()[...,1:],2,-1)**2)
        self.proj()


    def exp(self, lr):
        """ Exponential map """
        x = self.data.detach()
        # print("norm", HyperboloidParameter.norm_h(x))
        v = -lr * self.grad

        retract = False
        if retract:
        # retraction
            # print("retract")
            self.data = x + v

        else:
            # print("tangent", HyperboloidParameter.dot_h(x, v))
            assert torch.all(1 - torch.isnan(v))
            n = self.__class__.norm_h(v).unsqueeze(-1)
            assert torch.all(1 - torch.isnan(n))
            n.clamp_(max=1.0)
            # e = torch.cosh(n)*x + torch.sinh(n)*v/n
            mask = torch.abs(n)<1e-7
            cosh = torch.cosh(n)
            cosh[mask] = 1.0
            sinh = torch.sinh(n)
            sinh[mask] = 0.0
            n[mask] = 1.0
            e = cosh*x + sinh/n*v
            # assert torch.all(-HyperboloidParameter.dot_h(e,e) >= 0), torch.min(-HyperboloidParameter.dot_h(e,e))
            self.data = e
        self.proj()


    def modify_grad_inplace(self):
        """ Convert Euclidean gradient into Riemannian """
        self.grad[...,0] *= -1
        #print("check data")
        #print(np.argwhere(torch.isnan(self.data).cpu().numpy()))
        #print("check grad")
        #print(np.argwhere(torch.isnan(self.grad).cpu().numpy()))


        # self.grad += self.__class__.dot_h(self.data, self.grad).unsqueeze(-1) * self.data
        self.grad -= self.__class__.dot_h(self.data, self.grad).unsqueeze(-1) / HyperboloidParameter.dot_h(self.data, self.data).unsqueeze(-1) * self.data

# TODO can use kwargs instead of pasting defaults
class HalfPlaneParameter(RParameter):
    def __new__(cls, data=None, requires_grad=True, sizes=None, exp=False):
        if sizes is not None:
            sizes = list(sizes)
            sizes[-1] += 1
        return super().__new__(cls, data, requires_grad, sizes, exp)

    @staticmethod
    def dot_h(x,y):
        return torch.sum(x * y, -1)
    @staticmethod
    def euclid_dot_h(x,y):
        return torch.sum(x * y, -1)
    @staticmethod
    def norm_h(x):
        # assert torch.all(HalfPlaneParameter.dot_h(x,x) >= 0), torch.min(HalfPlaneParameter.dot_h(x,x))
        return torch.sqrt(torch.clamp(HalfPlaneParameter.euclid_dot_h(x,x), min=0.0))
    @staticmethod
    def dist_h(x,y):
        # squared = HalfPlaneParameter.norm_h(y[...,:-1] - x[...,:-1]).pow(2)
        # y_minus_x = (y[...,-1] - x[...,-1]).pow(2)
        # y_plus_x = (y[...,-1] + x[...,-1]).pow(2)

        # val_minus = torch.sqrt(squared + y_minus_x)
        # val_plus = torch.sqrt(squared + y_plus_x)

        # import pdb
        # if any(torch.isnan(val_minus)) or any(torch.isnan(val_plus)):
        #     pdb.set_trace()

        # return 2 * torch.log((val_minus + val_plus) / (2*torch.sqrt(y[...,-1] * x[...,-1])))

        # equivalent calculation
        numerator = ((y - x) * (y - x)).sum(1)
        denominator = 2 * x[:, -1] * y[:, -1]
        return acosh(1 + numerator / denominator)

    @staticmethod
    def _proj(x):
        """ Project onto hyperboloid """
        x_ = torch.tensor(x)
        x_tail = x_[...,1:]
        current_norms = torch.norm(x_tail,2,-1)
        scale      = (current_norms/1e7).clamp_(min=1.0)
        x_tail /= scale.unsqueeze(-1)
        x_[...,1:] = x_tail
        x_[...,0] = torch.sqrt(1 + torch.norm(x_tail,2,-1)**2)

        debug = False
        if debug:
            bad = torch.min(-HyperboloidParameter.dot_h(x_,x_))
            if bad <= 0.0:
                print("way off hyperboloid", bad)
            assert torch.all(-HyperboloidParameter.dot_h(x_,x_) > 0.0), f"way off hyperboloid {torch.min(-HyperboloidParameter.dot_h(x_,x_))}"
        xxx = x_ / torch.sqrt(torch.clamp(-HyperboloidParameter.dot_h(x_,x_), min=0.0)).unsqueeze(-1)

        # AT THIS POINT, xxx is hyperboloid
        final_dim = xxx[...,-1]
        final_dim = np.reshape(final_dim, (-1,1))
        final_dim = 1 / final_dim

        xxx[:, -1] = 1
        xxx = xxx * final_dim

        # AT THIS POINT, xxx is hemisphere
        first_dim = xxx[...,0]
        first_dim = np.reshape(first_dim, (-1,1))

        xxx = 2 * xxx / (first_dim + 1)
        xxx[:, 0] = 1

        # AT THIS POINT, xxx is half plane
        return xxx

    def initial_proj(self):
        """ Project the initialization of the embedding onto the manifold """
        self.data[...,0] = torch.sqrt(1 + torch.norm(self.data.detach()[...,1:],2,-1)**2)
        self.proj()

    def modify_grad_inplace(self):
        ne = (self.data[:,-1] * self.data[:,-1]).view(-1, 1)
        self.grad = self.grad * ne
        self.grad.clamp_(min=-10000.0, max=10000.0)

# TODO:
# 1. Improve speed up of projection by making operations in place.
class PoincareParameter(RParameter):
    def __new__(cls, data=None, requires_grad=True, sizes=None, check_graph=False):
        ret =  super().__new__(cls, data, requires_grad, sizes)
        ret.check_graph = check_graph
        return ret

    def modify_grad_inplace(self):
        # d        = self.data.dim()
        w_norm   = torch.norm(self.data,2,-1, True)
        # This is the inverse of the remanian metric, which we need to correct for.
        hyper_b  = (1 - w_norm**2)**2/4
        # new_size = tuple([1] * (d - 1) + [self.data.size(d-1)])
        # self.grad   *= hyper_b.repeat(*new_size) # multiply pointwise
        self.grad   *= hyper_b # multiply pointwise
        self.grad.clamp_(min=-10000.0, max=10000.0)

        # We could do the projection here?
        # NB: THIS IS DEATHLY SLOW. FIX IT
        if self.check_graph and np.any(np.isnan(self.grad.data.cpu().numpy())):
             print(np.any(np.isnan(self.data.cpu().numpy())))
             print(np.any(np.isnan(self.grad.data.cpu().numpy())))
             print(np.any(np.isnan(w_norm.cpu().numpy())))
             raise ValueError("NaN During Hyperbolic")

    @staticmethod
    def _correct(x, eps=1e-10):
        current_norms = torch.norm(x,2,x.dim() - 1)
        mask_idx      = current_norms < 1./(1+eps)
        modified      = 1./((1+eps)*current_norms)
        modified[mask_idx] = 1.0
        #new_size      = [1]*current_norms.dim() + [x.size(x.dim()-1)]
        #return modified.unsqueeze(modified.dim()).repeat(*new_size)
        # return modified.unsqueeze(modified.dim()).expand(x.size())
        return modified.unsqueeze(-1)

    @staticmethod
    def _proj(x, eps=1e-10):
        return x * PoincareParameter._correct(x, eps=eps)

    # def proj(self, eps=1e-10):
    #     self.data = self.__class__._proj(self.data.detach())#PoincareParameter._correct(self.data, eps=eps)

    def __repr__(self):
        return 'Hyperbolic parameter containing:' + self.data.__repr__()

class KleinParameter(RParameter):
    def __new__(cls, data=None, requires_grad=True, sizes=None, check_graph=False, exp=False):
        ret =  super().__new__(cls, data, requires_grad, sizes, exp)

        ret.check_graph = check_graph
        return ret

    def modify_grad_inplace(self):
        w_norm   = torch.norm(self.data,2,-1, True)
        hyper_b   = 1 - w_norm**2
        self.grad   *= hyper_b # multiply pointwise
        self.grad.clamp_(min=-10.0, max=10.0)

    @staticmethod
    def _proj(x, eps=1e-10):
        if torch.max(torch.norm(x, p=2, dim=1)) >= 1.0:
            x /= (torch.max(torch.norm(x, p=2, dim=1)) + 1e-3)
        return x

        """ Project onto hyperboloid """
        x_ = torch.tensor(x)
        x_tail = x_[...,1:]
        current_norms = torch.norm(x_tail,2,-1)
        scale      = (current_norms/1e7).clamp_(min=1.0)
        x_tail /= scale.unsqueeze(-1)
        x_[...,1:] = x_tail
        x_[...,0] = torch.sqrt(1 + torch.norm(x_tail,2,-1)**2)

        xxx = x_ / torch.sqrt(torch.clamp(-HyperboloidParameter.dot_h(x_,x_), min=0.0)).unsqueeze(-1)

        # AT THIS POINT, xxx is hyperboloid
        final_dim = xxx[...,-1]
        final_dim = np.reshape(final_dim, (-1,1))
        final_dim = 1 / final_dim

        xxx[:, -1] = 1
        xxx = xxx * final_dim

        # AT THIS POINT, xxx is hemisphere
        xxx[:, -1] = 1

        # AT THIS POINT, xxx is half plane
        return xxx
    @staticmethod
    def _dist_h(p,q):
        if torch.norm(p-q) < 1e-4:
            return 1e-5
        aval = (-1.0*torch.dot(p-q,q) + torch.sqrt( (torch.dot(p-q,q))**2  - torch.norm(p-q)**2 * (torch.norm(q)**2-1) )) / torch.norm(p-q) **2
        bval = (-1.0*torch.dot(p-q,q) - torch.sqrt( (torch.dot(p-q,q))**2  - torch.norm(p-q)**2 * (torch.norm(q)**2-1) )) / torch.norm(p-q) **2
        a = aval*(p-q) + q
        b = bval*(p-q) + q
        return torch.clamp(0.5 * torch.log(torch.norm(torch.abs(p-b)) * torch.norm(torch.abs(q-a)) / (torch.norm(torch.abs(p-a)) * torch.norm(torch.abs(q-b)))), 1e-5)
    @staticmethod
    def dist_h(x,y):
        n = y.shape[0]
        dists = torch.zeros([n], dtype=torch.double)
        for i in range(n):
            dists[i] = KleinParameter._dist_h(x[0], y[i])
        #print("x[0] = ", x[0])
        #print("y[i] = ", y[i])
        #print(dists)
        return dists
    def exp(self, lr):
        """ Exponential map """
        x = self.data.detach()
        v = -lr * self.grad

        # assert torch.all(1 - torch.isnan(v))
        # n = self.__class__.norm_h(v).unsqueeze(-1)
        # assert torch.all(1 - torch.isnan(n))
        # n.clamp_(max=1.0)
        v += x
        v_norm = torch.norm(v)
        e = v * (torch.sinh(v_norm) / torch.cosh(v_norm))
        self.data = e
        self.proj()

    def __repr__(self):
        return 'Klein parameter containing:' + self.data.__repr__()

class SphericalParameter(RParameter):
    def __new__(cls, data=None, requires_grad=True, sizes=None, exp=True):
        if sizes is not None:
            sizes = list(sizes)
            sizes[-1] += 1
        return super().__new__(cls, data, requires_grad, sizes, exp)


    def modify_grad_inplace(self):
        """ Convert Euclidean gradient into Riemannian by projecting onto tangent space """
        # pass
        self.grad -= dot(self.data, self.grad).unsqueeze(-1) * self.data

    def exp(self, lr):
        x = self.data.detach()
        v = -lr*self.grad

        retract = False
        if retract:
        # retraction
            self.data = x + v

        else:
            n = torch.norm(v, 2, -1, keepdim=True)
            mask = torch.abs(n)<1e-7
            cos = torch.cos(n)
            cos[mask] = 1.0
            sin = torch.sin(n)
            sin[mask] = 0.0
            n[torch.abs(n)<1e-7] = 1.0
            e = cos*x + sin*v/n
            self.data = e
        self.proj()

    @staticmethod
    def _proj(x):
        # return x / torch.norm(x, 2, -1).unsqueeze(-1)
        return x / torch.norm(x, 2, -1, True)

    # def proj(self):
    #     x = self.data.detach()
    #     self.data = SphericalParameter._proj(x)
    def initial_proj(self):
        # pass
        self.data[...,0] = torch.sqrt(1 - torch.norm(self.data[...,1:],2,-1)**2)

class EuclideanParameter(RParameter):
    def proj(x):
        pass
