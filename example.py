import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
import cv2

from camera import Camera
import structure
import processor
import features


input_path = 'house/'
camera_filepath = 'house/3D/house.00{0}.P'

cameras = [Camera(processor.read_matrix(camera_filepath.format(i))) for i in range(9)]
[c.factor() for c in cameras]

points3d = processor.read_matrix('house/3D/house.p3d').T  # 3 x n
points4d = np.vstack((points3d, np.ones(points3d.shape[1])))  # 4 x n
points2d = [processor.read_matrix(input_path + '2D/house.00' + str(i) + '.corners') for i in range(9)]

index1 = 2
index2 = 4
img1 = cv2.imread(input_path + 'house.00' + str(index1) + '.pgm')  # left image
img2 = cv2.imread(input_path + 'house.00' + str(index2) + '.pgm')
x = cameras[index2].project(points4d)

# fig = plt.figure()
# ax = fig.gca(projection='3d')
# ax.plot(points3d[0], points3d[1], points3d[2], 'b.')
# ax.set_xlabel('x axis')
# ax.set_ylabel('y axis')
# ax.set_zlabel('z axis')
# ax.view_init(elev=135, azim=90)

# plt.figure()
# plt.plot(x[0], x[1], 'b.')
# plt.show()

corner_indexes = processor.read_matrix(input_path + '2D/house.nview-corners', np.int)
corner_indexes1 = corner_indexes[:, index1]
corner_indexes2 = corner_indexes[:, index2]
intersect_indexes = np.intersect1d(np.nonzero([corner_indexes1 != -1]), np.nonzero([corner_indexes2 != -1]))
corner_indexes1 = corner_indexes1[intersect_indexes]
corner_indexes2 = corner_indexes2[intersect_indexes]
points1 = processor.cart2hom(points2d[index1][corner_indexes1].T)
points2 = processor.cart2hom(points2d[index2][corner_indexes2].T)
print(points1.shape, points2.shape)

height, width, ch = img1.shape
intrinsic = np.array([ # for imgs/house
    [2362.12, 0, width / 2],
    [0, 2366.12, height / 2],
    [0, 0, 1]])

# Dino
img1 = cv2.imread('imgs/dinos/viff.002.ppm')
img2 = cv2.imread('imgs/dinos/viff.001.ppm')
pts1, pts2 = features.find_correspondence_points(img1, img2)
points1 = processor.cart2hom(pts1)
points2 = processor.cart2hom(pts2)

plt.subplot(1, 2, 1)
plt.imshow(img1)
plt.plot(points1[0], points1[1], 'r.')
plt.subplot(1, 2, 2)
plt.imshow(img2)
plt.plot(points2[0], points2[1], 'r.')
plt.show()

height, width, ch = img1.shape
K = np.array([ # for dino
    [1200, 0, width / 2],
    [0, 1200, height / 2],
    [0, 0, 1]])

# Calculate essential matrix with 2d points.
# Result will be up to a scale
# First, normalize points
points1n = np.dot(np.linalg.inv(intrinsic), points1)
points2n = np.dot(np.linalg.inv(intrinsic), points2)
E = structure.compute_essential_normalized(points1n, points2n)
print('Computed essential matrix:', (-E / E[0][1]))

# Given we are at camera 1, calculate the parameters for camera 2
# Using the essential matrix returns 4 possible camera paramters
P1 = np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0]])
P2s = structure.compute_P_from_essential(E)

ind = -1
for i, P2 in enumerate(P2s):
    # Find the correct camera parameters
    d1 = structure.reconstruct_one_point(points1n[:, 0], points2n[:, 0], P1, P2)

    # Convert P2 from camera view to world view
    P2_homogenous = np.linalg.inv(np.vstack([P2, [0, 0, 0, 1]]))
    d2 = np.dot(P2_homogenous[:3, :4], d1)

    if d1[2] > 0 and d2[2] > 0:
        ind = i

P2 = np.linalg.inv(np.vstack([P2s[ind], [0, 0, 0, 1]]))[:3, :4]
print(ind, P2)
tripoints3d = structure.reconstruct_points(points1n, points2n, P1, P2)
tripoints3d2 = structure.linear_triangulation(points1n, points2n, P1, P2)

print(tripoints3d[:,1], tripoints3d2[:,1])
fig = plt.figure()
ax = fig.gca(projection='3d')
ax.plot(tripoints3d[0], tripoints3d[1], tripoints3d[2], 'b.')
ax.set_xlabel('x axis')
ax.set_ylabel('y axis')
ax.set_zlabel('z axis')
ax.view_init(elev=135, azim=90)
plt.show()