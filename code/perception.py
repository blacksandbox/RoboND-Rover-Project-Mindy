import numpy as np
import cv2

# Identify pixels above the threshold
# Threshold of RGB > 160 does a nice job of identifying ground pixels only
def color_thresh(img, rgb_thresh=(160, 160, 160)):
    # Create an array of zeros same xy size as img, but single channel
    color_select = np.zeros_like(img[:,:,0])
    # Require that each pixel be above all three threshold values in RGB
    # above_thresh will now contain a boolean array with "True"
    # where threshold was met
    above_thresh = (img[:,:,0] > rgb_thresh[0]) \
                & (img[:,:,1] > rgb_thresh[1]) \
                & (img[:,:,2] > rgb_thresh[2])
    # Index the array of zeros with the boolean array and set to 1
    color_select[above_thresh] = 1
    # Return the binary image
    return color_select

# Define a function to convert to rover-centric coordinates
def rover_coords(binary_img):
    # Identify nonzero pixels
    ypos, xpos = binary_img.nonzero()
    # Calculate pixel positions with reference to the rover position being at the 
    # center bottom of the image.  
    x_pixel = np.absolute(ypos - binary_img.shape[0]).astype(np.float)
    y_pixel = -(xpos - binary_img.shape[0]).astype(np.float)
    return x_pixel, y_pixel


# Define a function to convert to radial coords in rover space
def to_polar_coords(x_pixel, y_pixel):
    # Convert (x_pixel, y_pixel) to (distance, angle) 
    # in polar coordinates in rover space
    # Calculate distance to each pixel
    dist = np.sqrt(x_pixel**2 + y_pixel**2)
    # Calculate angle away from vertical for each pixel
    angles = np.arctan2(y_pixel, x_pixel)
    return dist, angles

# Define a function to apply a rotation to pixel positions
def rotate_pix(xpix, ypix, yaw):
    
    # Convert yaw to radians
    yr = yaw*(np.pi/180)

    # Apply a rotation
    xpix_rotated = xpix*np.cos(yr) - ypix*np.sin(yr)
    ypix_rotated = xpix*np.sin(yr) + ypix*np.cos(yr)
    
    # Return the result  
    return xpix_rotated, ypix_rotated

# Define a function to perform a translation
def translate_pix(xpix_rot, ypix_rot, xpos, ypos, scale):
    xpix_translated = (xpix_rot / scale) + xpos
    ypix_translated = (ypix_rot / scale) + ypos
        
    # Apply a scaling and a translation
    return xpix_translated, ypix_translated

# Define a function to apply rotation and translation (and clipping)
# Once you define the two functions above this function should work
def pix_to_world(xpix, ypix, xpos, ypos, yaw, world_size, scale):
    # Apply rotation
    xpix_rot, ypix_rot = rotate_pix(xpix, ypix, yaw)
    # Apply translation
    xpix_tran, ypix_tran = translate_pix(xpix_rot, ypix_rot, xpos, ypos, scale)
    # Perform rotation, translation and clipping all at once
    x_pix_world = np.clip(np.int_(xpix_tran), 0, world_size - 1)
    y_pix_world = np.clip(np.int_(ypix_tran), 0, world_size - 1)
    # Return the result
    return x_pix_world, y_pix_world

# Define a function to perform a perspective transform
def perspect_transform(img, src, dst):
           
    M = cv2.getPerspectiveTransform(src, dst)
    warped = cv2.warpPerspective(img, M, (img.shape[1], img.shape[0]))# keep same size as input image
    
    return warped


# Identify pixels above the threshold
# Threshold of RGB > 160 does a nice job of identifying ground pixels only
def color_thresh(img, rgb_thresh=(160, 160, 160)):
    # Empty array
    color_select = np.zeros_like(img[:,:,0]) 

    # Make boolean array where it is above threshold
    above_thresh = (img[:,:,0] > rgb_thresh[0]) \
                & (img[:,:,1] > rgb_thresh[1]) \
                & (img[:,:,2] > rgb_thresh[2])

    color_select[above_thresh] = 1

    return color_select

def color_thresh_inverted(img, rgb_thresh=(160, 160, 160)):
    # Empty array
    color_select = np.zeros_like(img[:,:,0])
    
    # Make boolean array where it contain image (meaning, not black)
    has_val = (img[:,:,0] > 0) \
              & (img[:,:,1] > 0) \
              & (img[:,:,2]> 0)

    # Make boolean array where it contain image (meaning, not black)
    below_thresh = (img[:,:,0] < rgb_thresh[0]) \
                & (img[:,:,1] < rgb_thresh[1]) \
                & (img[:,:,2] < rgb_thresh[2])
    # Index the array of zeros with the boolean array and set to 1
    color_select[below_thresh] = 1
    color_select = color_select*has_val
    # Return the binary image
    return color_select

def standardize_HSV_vals(hsv_vals=(-1,-1,-1)):
    
    if hsv_vals[0] == -1:
        return -1
    
    max_vals = (360, 100, 100)
    max_vals_converted = (179, 255, 255)
  
    vals_converted = []
    for i in range(3):
        val_before = hsv_vals[i]
        val_after = (val_before/max_vals[i]) * max_vals_converted[i]
        vals_converted.append(np.rint(val_after))
  
    return vals_converted

def rock_threshed(img):
    
    # Convert BGR to HSV
    hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)

    # Threshold the HSV image to get the rock sample color
    # Used this to get estimates of yellow in the simulator: http://imagecolorpicker.com/
    lower_yellow = np.array(
        standardize_HSV_vals(hsv_vals=(40, 50, 50)),
        dtype = "uint8"
    )
    upper_yellow = np.array(
        standardize_HSV_vals(hsv_vals=(50, 100, 100)),
        dtype = "uint8"
    )
    mask = cv2.inRange(hsv, lower_yellow, upper_yellow)
    #mask = cv2.cvtColor(mask, cv2.COLOR_HSV2RGB) #looks like I am not supposed to do this
    return mask 

import matplotlib.image as mpimg

# Apply the above functions in succession and update the Rover state accordingly
def perception_step(Rover):
    # Perform perception steps to update Rover()
    # TODO: 
    # NOTE: camera image is coming to you in Rover.img

    # 1) Define source and destination points for perspective transform
    # 2) and apply perspective transform
    dst_size = 5 
    bottom_offset = 6
    source = np.float32([[35, 136], [293 ,136],[202, 97], [120, 97]])
    destination = np.float32([[Rover.img.shape[1]/2 - dst_size, Rover.img.shape[0] - bottom_offset],
                                [Rover.img.shape[1]/2 + dst_size, Rover.img.shape[0] - bottom_offset],
                      [Rover.img.shape[1]/2 + dst_size, Rover.img.shape[0] - 2*dst_size - bottom_offset], 
                      [Rover.img.shape[1]/2 - dst_size, Rover.img.shape[0] - 2*dst_size - bottom_offset],
                      ])
    img_warped = perspect_transform(Rover.img, source, destination)


    # 3) Apply color threshold to identify navigable terrain/obstacles/rock samples
    # 4) Update Rover.vision_image (this will be displayed on left side of screen)
    threshed_terrain_fullsighted = color_thresh(img_warped) #used later for settng rover's direction
    threshed_terrain_fullsighted[0:30,:] = 0
    threshed_terrain = np.copy(threshed_terrain_fullsighted)
    threshed_terrain[0:90,:] = 0 #this is for increasing fidelity on the worldmap
    threshed_obstacle = color_thresh_inverted(img_warped)
    threshed_rock = rock_threshed(img_warped)
    #threshed_terrain[0:100,:] = 0

    Rover.vision_image = np.dstack((threshed_obstacle*255, threshed_rock*255, threshed_terrain*255)).astype(np.float)

    # 5) Convert map image pixel values to rover-centric coords
    navigable_x, navigable_y = rover_coords(threshed_terrain)
    obstacle_x, obstacle_y = rover_coords(threshed_obstacle)
    rock_x, rock_y = rover_coords(threshed_rock)

    # 6) Convert rover-centric pixel values to world coordinates
    scale = 10.0
    navigable_x_world, navigable_y_world = pix_to_world(navigable_x, navigable_y, Rover.pos[0], Rover.pos[1], 
                                                        Rover.yaw, Rover.worldmap.shape[0], scale)
    obstacle_x_world, obstacle_y_world =   pix_to_world(obstacle_x, obstacle_y, Rover.pos[0], Rover.pos[1], 
                                                        Rover.yaw, Rover.worldmap.shape[0], scale)
    rock_x_world, rock_y_world =           pix_to_world(rock_x, rock_y, Rover.pos[0], Rover.pos[1], 
                                                        Rover.yaw, Rover.worldmap.shape[0], scale)


    # 7) Update Rover worldmap (to be displayed on right side of screen)
    #testImg = mpimg.imread('../calibration_images/map_bw2.png')
    #Rover.worldmap = np.dstack((testImg*255, testImg*0, testImg*0)).astype(np.float)

    #check if it is "safe" to update the world map
    pitch_thresh = 2.00
    roll_thresh = 1.20
    
    if (Rover.pitch < pitch_thresh or Rover.pitch > 360 - pitch_thresh):
        if (Rover.roll < roll_thresh or Rover.roll > 360 - roll_thresh):
            Rover.worldmap[obstacle_y_world, obstacle_x_world, 0] += 1
            Rover.worldmap[rock_y_world, rock_x_world, 1] = 255
            Rover.worldmap[navigable_y_world, navigable_x_world, 2] += 1


    # 8) Convert rover-centric pixel positions to polar coordinates
    # Update Rover pixel distances and angles


    navigable_x, navigable_y = rover_coords(threshed_terrain_fullsighted)
    Rover.nav_dists, Rover.nav_angles = to_polar_coords(navigable_x, navigable_y)

    
    return Rover

