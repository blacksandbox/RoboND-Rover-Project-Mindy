# Define a function to pass stored images to
# reading rover position and yaw angle from csv file
# This function will be used by moviepy to create an output video
def process_image(img, single_image=False):
    # Example of how to use the Databucket() object defined above
    # to print the current x, y and yaw values 
    # print(data.xpos[data.count], data.ypos[data.count], data.yaw[data.count])

    # TODO: 
    
    # 1) Define source and destination points for perspective transform
    # 2) Apply perspective transform
    img_warped = perspect_transform(img, source, destination)
    
    # 3) Apply color threshold to identify navigable terrain/obstacles/rock samples
    threshed_terrain = color_thresh(img_warped)
    threshed_obstacle = color_thresh_inverted(img_warped)
    threshed_rock = rock_threshed(img_warped)
    
    threshed_terrain[0:100,:] = 0
    
    # 4) Convert thresholded image pixel values to rover-centric coords
    navigable_x, navigable_y = rover_coords(threshed_terrain)
    obstacle_x, obstacle_y = rover_coords(threshed_obstacle)
    rock_x, rock_y = rover_coords(threshed_rock)
    
    # 5) Convert rover-centric pixel values to world coords
    scale = 10.0
    
#     if single_image:
#         data.xpos = [107.2932]
#         data.ypos = [55.38367]
#         data.yaw = [282.0622]

    navigable_x_world, navigable_y_world = pix_to_world(navigable_x, navigable_y, 
                                                        data.xpos, data.ypos, 
                                                        data.yaw, data.worldmap.shape[0], scale,
                                                       single_image)
    obstacle_x_world, obstacle_y_world = pix_to_world(obstacle_x, obstacle_y, 
                                                      data.xpos, data.ypos, 
                                                      data.yaw, data.worldmap.shape[0], scale,
                                                     single_image)
    rock_x_world, rock_y_world = pix_to_world(rock_x, rock_y, 
                                              data.xpos, data.ypos, 
                                              data.yaw, data.worldmap.shape[0], scale,
                                             single_image)



    # 6) Update worldmap (to be displayed on right side of screen)
#     data.worldmap[obstacle_y_world, obstacle_x_world, 0] = 150
#     data.worldmap[rock_y_world, rock_x_world, 1] = 255
#     data.worldmap[navigable_y_world, navigable_x_world, 2] = 255
    
    data.worldmap[obstacle_y_world, obstacle_x_world, 0] += 1
    data.worldmap[rock_y_world, rock_x_world, 1] = 255
    data.worldmap[navigable_y_world, navigable_x_world, 2] = 255
    
    #remove obstacle when there isn't one. Is that possible?
    
    threshed_view = np.dstack((threshed_obstacle*255, threshed_rock*255, threshed_terrain*255)).astype(np.float)
    
    cam_view = np.zeros((200, 200, 3)).astype(np.float)
    cam_view[obstacle_y_world, obstacle_x_world, 0] = 160
    #cam_view[rock_y_world, rock_x_world, 1] = 255
    cam_view[navigable_y_world, navigable_x_world, 2] = 255


    # 7) Make a mosaic image, below is some example code
        # First create a blank image (can be whatever shape you like)
    output_image = np.zeros((img.shape[0] + data.worldmap.shape[0], img.shape[1]*2, 3))
        # Next you can populate regions of the image with various output
        # Here I'm putting the original image in the upper left hand corner
    output_image[0:img.shape[0], 0:img.shape[1]] = img

        # Let's create more images to add to the mosaic, first a warped image
    warped = img_warped
        # Add the warped image in the upper right hand corner
    #output_image[0:img.shape[0], img.shape[1]:] = np.dstack((threshed_terrain*0, threshed_terrain*255, threshed_terrain*0)).astype(np.float)
    output_image[0:img.shape[0], img.shape[1]:] = threshed_view 
        # Overlay worldmap with ground truth map
    map_add = cv2.addWeighted(data.worldmap, 1, data.ground_truth, 0.5, 0)
        # Flip map overlay so y-axis points upward and add to output_image 
    output_image[img.shape[0]:, 0:data.worldmap.shape[1]] = np.flipud(map_add)
    
    
    output_image[img.shape[0]:img.shape[0]+data.worldmap.shape[0],
                 data.worldmap.shape[1]:data.worldmap.shape[1]*2] = cam_view
    

        # Then putting some text over the image
    cv2.putText(output_image,"Frame: %d" % data.count, (20, 20), 
                cv2.FONT_HERSHEY_COMPLEX, 0.4, (255, 255, 255), 1)
    data.count += 1 # Keep track of the index in the Databucket()
    
    return output_image

#tester
# Grab one frame 
#image = mpimg.imread('../calibration_images/world_test.jpg')
#output_image = process_image(image, True)

# fig = plt.figure(figsize=(12,9))
# plt.subplot(221)
# plt.imshow(output_image)
print("done")