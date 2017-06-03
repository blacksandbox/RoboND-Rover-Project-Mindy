import numpy as np


# This is where you can build a decision tree for determining throttle, brake and steer 
# commands based on the output of the perception_step() function
def decision_step(Rover):

    # Implement conditionals to decide what to do given perception data
    # Here you're all set up with some basic functionality but you'll need to
    # improve on this decision tree to do a good job of navigating autonomously!

    # Example:
    # Check if we have vision data to make decisions with
    
    if Rover.nav_angles is not None:
        
        # First, check if the rover is stuck
        if Rover.is_stuck:
            #force rover to back up a little bit for about 100 frames
            if Rover.stuck_frame_count < 100:
                Rover.steer = 15
                Rover.throttle = Rover.throttle_set *(-1)
                Rover.stuck_frame_count += 1
            else:
                # Return rover to a regular mode.
                # Hopefully the rover has given a second chance.
                Rover.stuck_frame_count = 0
                Rover.mode = 'stop'
                Rover.throttle = 0
                Rover.is_stuck = False

        # Then, check for Rover.mode status
        elif Rover.mode == 'forward': 
            # Check the extent of navigable terrain
            if len(Rover.nav_angles) >= Rover.stop_forward:
                # If mode is forward, navigable terrain looks good 
                # and velocity is below max, then throttle 
                if Rover.vel < Rover.max_vel:
                    # Set throttle value to throttle setting
                    Rover.throttle = Rover.throttle_set
                else: # Else coast
                    Rover.throttle = 0
                Rover.brake = 0
                # Set steering to average angle clipped to the range +/- 15
                Rover.steer = np.clip(np.mean(Rover.nav_angles * 180/np.pi), -15, 15)


                #try to remember how well you've been moving forward
                if is_stuck(Rover):
                    print("ROVER MAY BE STUCK")
                    Rover.is_stuck = True
                

            # If there's a lack of navigable terrain pixels then go to 'stop' mode
            elif len(Rover.nav_angles) < Rover.stop_forward:
                    # Set mode to "stop" and hit the brakes!
                    Rover.throttle = 0
                    # Set brake to stored brake value
                    Rover.brake = Rover.brake_set
                    Rover.steer = 0
                    Rover.mode = 'stop'
  

        # If we're already in "stop" mode then make different decisions
        elif Rover.mode == 'stop':
            #Reset location memory
            Rover.pos_memory[0][:] = []
            Rover.pos_memory[1][:] = []

            # If we're in stop mode but still moving keep braking
            if Rover.vel > 0.2:
                Rover.throttle = 0
                Rover.brake = Rover.brake_set
                Rover.steer = 0
            # If we're not moving (vel < 0.2) then do something else
            elif Rover.vel <= 0.2:
                # Now we're stopped and we have vision data to see if there's a path forward
                if len(Rover.nav_angles) < Rover.go_forward:
                    Rover.throttle = 0
                    # Release the brake to allow turning
                    Rover.brake = 0
                    # Turn range is +/- 15 degrees, when stopped the next line will induce 4-wheel turning
                    Rover.steer = -15 # Could be more clever here about which way to turn
                # If we're stopped but see sufficient navigable terrain in front then go!
                if len(Rover.nav_angles) >= Rover.go_forward:
                    # Set throttle back to stored value
                    Rover.throttle = Rover.throttle_set
                    # Release the brake
                    Rover.brake = 0
                    # Set steer to mean angle
                    Rover.steer = np.clip(np.mean(Rover.nav_angles * 180/np.pi), -15, 15)
                    Rover.mode = 'forward'
    # Just to make the rover do something 
    # even if no modifications have been made to the code
    else:
        Rover.throttle = 0 #Rover.throttle_set
        Rover.steer = 0
        Rover.brake = 0
        
    # If in a state where want to pickup a rock send pickup command
    if Rover.near_sample and Rover.vel == 0 and not Rover.picking_up:
        Rover.send_pickup = True
    
    return Rover



def is_stuck(Rover):


    Rover.pos_memory[0].append(Rover.pos[0])
    Rover.pos_memory[1].append(Rover.pos[1])

    memory_limit = 300
    if len(Rover.pos_memory[0]) > memory_limit:
        Rover.pos_memory[0].pop(0)
        Rover.pos_memory[1].pop(0)

        # Compare robot's position with last 200 locations
        avg_pos = [
                    sum(Rover.pos_memory[0])/len(Rover.pos_memory[0]),
                    sum(Rover.pos_memory[1])/len(Rover.pos_memory[1])
                    ]
        curr_pos = np.copy(Rover.pos)
        avg_pos = np.array(avg_pos)
        unit_size = np.array([10,10])

        # "How am i doing?"
        movement_quality = np.absolute(curr_pos - avg_pos) / unit_size
        quality_threshold = 0.01
        print(movement_quality)
        if movement_quality[0] <= quality_threshold and movement_quality[1] <= quality_threshold:
            # I think you might be stuck
            return True
        else:
            # I don't think you are stuck
            return False

    else:
        #not enough information collected
        return False
