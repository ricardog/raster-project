from numba import jit, guvectorize, float64, int64
import numpy as np

@guvectorize([(float64[:], float64[:], float64[:], int64[:], float64[:])],
             '(), (m), (n), () -> (m)',
             cache=True, nopython=True)
def ortho_poly_predict(x, norm2, alpha, degree, Z):
  Z[0] = 1
  if degree[0] > 0:
    Z[1] = x[0] - alpha[0]
  if degree[0] > 1:
    for i in np.arange(1, degree[0]):
      Z[i+1] = (x[0] - alpha[i]) * Z[i] - (norm2[i] / norm2[i-1]) * Z[i-1]
  Z /= np.sqrt(norm2)

@guvectorize([(float64[:], float64[:], float64[:], int64[:], float64[:])],
             '(), (m), (n), () -> (m)',
             cache=True, nopython=True)
def ortho_poly_predict_(x, norm2, alpha, degree, Z):
  n2 = norm2 * norm2
  Z[0] = 1
  if degree[0] > 0:
    Z[1] = x[0] - alpha[0]
  if degree[0] > 1:
    for i in np.arange(1, degree[0]):
      Z[i+1] = (x[0] - alpha[i]) * Z[i] - (n2[i] / n2[i-1]) * Z[i-1]
  Z /= norm2
  
@jit()
def ortho_poly_predict_idx(x, norm2, alpha, degree = 1):
  n = degree + 1
  Z = np.empty((len(x), n))
  for idx in np.arange(len(x)):
    Z[idx:, 0] = 1
    if degree > 0:
      Z[idx:, 1] = x[idx] - alpha[0]
    if degree > 1:
      for i in np.arange(1,degree):
        Z[idx:, i+1] = (x[idx] - alpha[i]) * Z[idx:, i] - (norm2[i] / norm2[i-1]) * Z[idx:, i-1]
  Z /= np.sqrt(norm2)
  return Z
