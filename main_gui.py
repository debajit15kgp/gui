import os, pygame
from pygame.locals import *
from pygame.compat import geterror

if not pygame.font: print('Warning, fonts disabled')
if not pygame.mixer: print('Warning, sound disabled')

import rospy,sys
from utils.geometry import Vector2D
from utils.functions import *
from krssg_ssl_msgs.msg import point_2d
from krssg_ssl_msgs.msg import BeliefState
from krssg_ssl_msgs.msg import gr_Commands
from krssg_ssl_msgs.msg import gr_Robot_Command
#from krssg_ssl_msgs.msg import BeliefState
#from role import  GoToBall, GoToPoint
from multiprocessing import Process
from kubs import kubs
#from krssg_ssl_msgs.srv import bsServer
from math import atan2,pi
from utils.functions import *
pub = rospy.Publisher('/grsim_data',gr_Commands,queue_size=1000)


main_dir = os.path.split(os.path.abspath(__file__))[0]
data_dir = os.path.join(main_dir, 'data')

print(os.getcwd())
rospy.init_node('node',anonymous=False)
start_time = rospy.Time.now()
start_time = 1.0*start_time.secs + 1.0*start_time.nsecs/pow(10,9)   

# functions to create our resources
# def load_image(name, colorkey=None):
#     fullname = os.path.join(data_dir, name)
#     try:
#         image = pygame.image.load(fullname)
#     except pygame.error:
#         print('Cannot load image:', fullname)
#         raise SystemExit(str(geterror()))
#     image = image.convert()
#     if colorkey is not None:
#         if colorkey == -1:
#             colorkey = image.get_at((0, 0))
#         image.set_colorkey(colorkey, RLEACCEL)
#     return image, image.get_rect()





# # classes for our game objects
# class Fist(pygame.sprite.Sprite):
#     """moves a clenched fist on the screen, following the mouse"""
#     def __init__(self):
#         pygame.sprite.Sprite.__init__(self) #call Sprite initializer
#         self.image, self.rect = load_image('b.bmp', -1)
#         self.punching = 0

#     def update(self):
#         """move the fist based on the mouse position"""
#         pos = pygame.mouse.get_pos()
#         self.rect.midtop = pos
#         if self.punching:
#             self.rect.move_ip(5, 10)

#     def punch(self, target):
#         """returns true if the fist collides with the target"""
#         if not self.punching:
#             self.punching = 1
#             hitbox = self.rect.inflate(-5, -5)
#             return hitbox.colliderect(target.rect)

#     def unpunch(self):
#         """called to pull the fist back"""
#         self.punching = 0


# class Chimp(pygame.sprite.Sprite):
#     """moves a monkey critter across the screen. it can spin the
#        monkey when it is punched."""
#     def __init__(self):
#         pygame.sprite.Sprite.__init__(self)  # call Sprite intializer
#         self.image, self.rect = load_image('a_1.bmp', -1)
#         screen = pygame.display.get_surface()
#         self.area = screen.get_rect()
#         self.rect.topleft = 10, 10
#         self.move = 9
#         self.dizzy = 0

#     def update(self):
#         """walk or spin, depending on the monkeys state"""
#         if self.dizzy:
#             self._spin()
#         else:
#             self._walk()

#     def _walk(self):
#         """move the monkey across the screen, and turn at the ends"""
#         newpos = self.rect.move((self.move, 0))
#         if not self.area.contains(newpos):
#             if self.rect.left < self.area.left or \
#                     self.rect.right > self.area.right:
#                 self.move = -self.move
#                 newpos = self.rect.move((self.move, 0))
#                 self.image = pygame.transform.flip(self.image, 1, 0)
#             self.rect = newpos

#     def _spin(self):
#         """spin the monkey image"""
#         center = self.rect.center
#         self.dizzy = self.dizzy + 12
#         if self.dizzy >= 360:
#             self.dizzy = 0
#             self.image = self.original
#         else:
#             rotate = pygame.transform.rotate
#             self.image = rotate(self.original, self.dizzy)
#         self.rect = self.image.get_rect(center=center)

#     def punched(self):
#         """this will cause the monkey to start spinning"""
#         if not self.dizzy:
#             self.dizzy = 1
#             self.original = self.image

def send_command(pub, team, bot_id, v_x, v_y, v_w, kick_power, dribble, chip_power = 0):
	""" 
	Publish the command packet
	team : 'True' if the team is yellow 
	"""
	gr_command = gr_Robot_Command()
	final_command = gr_Commands()
	
	"""
	Set the command to each bot
	"""
	gr_command.id          = bot_id
	gr_command.wheelsspeed = 0
	gr_command.veltangent  = v_x/1000
	gr_command.velnormal   = v_y/1000
	gr_command.velangular  = v_w
	gr_command.kickspeedx  = kick_power
	gr_command.kickspeedz  = chip_power
	gr_command.spinner     = dribble

	final_command.timestamp      = rospy.get_rostime().secs
	final_command.isteamyellow   = team
	final_command.robot_commands = gr_command

	
	def debug():
		"""
		Log the commands
		"""
		print 'botid: {}: [{}]\n'.format(bot_id, final_command.timestamp)
		print 'vel_x: {}\nvel_y: {}\nvel_w: {}\n'.format(v_x, v_y, v_w)
		print 'kick_power: {}\nchip_power: {}\ndribble_speed:{}\n\n'.format(kick_power, chip_power, dribble)
	
	# debug()
	pub.publish(final_command)


def main():
	power=False
	vx=0
	vy=0
	vw=0
	pygame.display.init()
	pygame.font.init()
	screen = pygame.display.set_mode((500, 500))
	pygame.display.set_caption('Monkey Fever')
	pygame.mouse.set_visible(0)

	# Create The Backgound
	background = pygame.Surface(screen.get_size())
	background = background.convert()
	background.fill((250, 250, 250))

	# Put Text On The Background, Centered
	if pygame.font:
		font = pygame.font.Font(None, 36)
		text = font.render("Pummel The Chimp, And Win $$$", 1, (10, 10, 10))
		textpos = text.get_rect(centerx=background.get_width()/2)
		background.blit(text, textpos)

	# Display The Background
	screen.blit(background, (0, 0))
	pygame.display.flip()

	# Prepare Game Objects
	clock = pygame.time.Clock()
	# chimp = Chimp()
	# fist = Fist()
	# allsprites = pygame.sprite.RenderPlain((fist, chimp))

	# Main Loop
	going = True
	while going:
		clock.tick(60)

		# Handle Input Events
		# for event in pygame.event.get():
		#     if event.type == QUIT:
		#         going = False
		#     elif event.type == KEYDOWN and event.key == K_ESCAPE:
		#         going = False
		#     elif event.type == MOUSEBUTTONDOWN:
		#         if fist.punch(chimp):
		#             punch_sound.play()  # punch
		#             chimp.punched()
		#         else:
		#             whiff_sound.play()  # miss
		#     elif event.type == MOUSEBUTTONUP:
		#         fist.unpunch()


		# Draw Everything
		screen.blit(background, (0, 0))
		#allsprites.draw(screen)
		pygame.display.flip()
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				pygame.quit(); sys.exit();pygame.display.quit()
				exit()
				#main = False

			pressed = pygame.key.get_pressed()
			if pressed[pygame.K_UP]:
				vx+=10
			if pressed[pygame.K_DOWN]:
				vx-=10
			if pressed[pygame.K_a]:
				vx=80
			if pressed[pygame.K_d]:
				vx=80
			if pressed[pygame.K_w]:  
				vy=80
			if pressed[pygame.K_s]:  
				vy=80
		   

			send_command(pub, True, 1, vx, vy, vw, power, False)

			
	pygame.display.quit()
	pygame.quit()
	#exit()

if __name__ == '__main__':
	main()


