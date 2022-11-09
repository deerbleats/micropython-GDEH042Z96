from machine import Pin, SPI
import framebuf
import utime

# Display resolution
EPD_WIDTH       = 400
EPD_HEIGHT      = 300

RST_PIN         = 27
DC_PIN          = 2
CS_PIN          = 14
BUSY_PIN        = 13



class EPD_4in2_B:
    def __init__(self):
        self.reset_pin = Pin(RST_PIN, Pin.OUT)
        
        self.busy_pin = Pin(BUSY_PIN, Pin.IN, Pin.PULL_UP)
        self.cs_pin = Pin(CS_PIN, Pin.OUT)
        self.width = EPD_WIDTH
        self.height = EPD_HEIGHT
        
        self.spi = SPI(2)
        self.spi.init(baudrate=1000_000)
        self.dc_pin = Pin(DC_PIN, Pin.OUT)
        
        
        self.buffer_black = bytearray(self.height * self.width // 8)
        self.buffer_red = bytearray(self.height * self.width // 8)
        self.imageblack = framebuf.FrameBuffer(self.buffer_black, self.width, self.height, framebuf.MONO_HLSB)
        self.imagered = framebuf.FrameBuffer(self.buffer_red, self.width, self.height, framebuf.MONO_HLSB)
        
        self.init()
        self.Clear()
        utime.sleep_ms(10)

    def digital_write(self, pin, value):
        pin.value(value)

    def digital_read(self, pin):
        return pin.value()

    def delay_ms(self, delaytime):
        utime.sleep(delaytime / 1000.0)

    def spi_writebyte(self, data):
        self.spi.write(bytearray(data))

    def module_exit(self):
        self.digital_write(self.reset_pin, 0)

    # Hardware reset
    def reset(self):
        self.digital_write(self.reset_pin, 0)
        self.delay_ms(10)
        self.digital_write(self.reset_pin, 1)
        self.delay_ms(10)


    def send_command(self, command):
        self.digital_write(self.dc_pin, 0)
        self.digital_write(self.cs_pin, 0)
        self.spi_writebyte([command])
        self.digital_write(self.cs_pin, 1)

    def send_data(self, data):
        self.digital_write(self.dc_pin, 1)
        self.digital_write(self.cs_pin, 0)
        self.spi_writebyte([data])
        self.digital_write(self.cs_pin, 1)
        
    def ReadBusy(self):
        print("busy")
        while(self.digital_read(self.busy_pin) == 1):
            self.delay_ms(100)    
        print("e-Paper busy release")
        
        
    def TurnOnDisplay(self):
        self.send_command(0x12)
        self.delay_ms(100) 
        self.ReadBusy()

            
    def init(self):
        # EPD hardware init start
        self.reset()
        
        self.ReadBusy()   
        self.send_command(0x12)  #SWRESET
        self.ReadBusy()   
        self.send_command(0x74)
        self.send_data(0x54)
        self.send_command(0x7E)
        self.send_data(0x3B)
        self.send_command(0x2B)
        self.send_data(0x04)         
        self.send_data(0x63)

        self.send_command(0x0C)
        self.send_data(0x8B)         
        self.send_data(0x9C)
        self.send_data(0x96)
        self.send_data(0x0F)

        self.send_command(0x01) 
        self.send_data(0x2B)
        self.send_data(0x01)
        self.send_data(0x00)

        self.send_command(0x11)  
        self.send_data(0x01)

        self.send_command(0x44)
        self.send_data(0x00)
        self.send_data(0x31)    

        self.send_command(0x45)        
        self.send_data(0x2B)   
        self.send_data(0x01)
        self.send_data(0x00)
        self.send_data(0x00) 

        self.send_command(0x3C) 
        self.send_data(0x01)

        self.send_command(0x18) 
        self.send_data(0x80)

        self.send_command(0x22)
        self.send_data(0XB1); 
        self.send_command(0x20)
        self.ReadBusy()

        self.send_command(0x4E)   
        self.send_data(0x00)
        self.send_command(0x4F)   
        self.send_data(0x2B)
        self.send_data(0x01)
        self.ReadBusy()
        #return 0
            
    def Clear(self):
        self.send_command(0x24)
        for i in range(0, int(self.width * self.height / 8)):
            self.send_data(0xFF)
            
        self.send_command(0x26) 
        for i in range(0, int(self.width * self.height / 8)):
            self.send_data(0x00)

        self.send_command(0x22) 
        self.send_data(0xC7)
        self.send_command(0x20) 
        self.ReadBusy()

    def EPD_4IN2B_Display(self,blackImage,redImage):
        high = self.height
        if( self.width % 8 == 0) :
            wide =  self.width // 8
        else :
            wide =  self.width // 8 + 1
                
        self.send_command(0x24)
        for j in range(0, high):
            for i in range(0, wide):
                self.send_data(blackImage[i + j * wide])
                
        self.send_command(0x26)
        for j in range(0, high):
            for i in range(0, wide):
                self.send_data(redImage[i + j * wide])
                
        self.TurnOnDisplay()
        
    def display(self, blackimage, redimage):
        # send black data
        if (blackimage != None):
            self.send_command(0x24) # DATA_START_TRANSMISSION_1
            for i in range(0, int(self.width * self.height / 8)):
                self.send_data(blackimage[i])
                if int(blackimage[i]) != 255: 
                    print(blackimage[i])
                else:
                    pass
                
        # send red data        
        if (redimage != None):
            self.send_command(0x26) # DATA_START_TRANSMISSION_2
            for i in range(0, int(self.width * self.height / 8)):
                self.send_data(redimage[i])  

        self.send_command(0x22) # DISPLAY_REFRESH
        self.send_data(0xC7)
        self.send_command(0x20) # DISPLAY_REFRESH
        self.ReadBusy()




    """
    def test_test(self):
        t = 0
        ad = -50
        r_l = list(self.buffer_black)
        test_r = []
        for l in range(0,300):
            ad = ad+50
            for l in range(ad,ad+50):
                test_r.insert(t,r_l[l])
                t = t+1
                if t ==50:
                    t = 0
        return test_r

    """
    def test_blk(self):
        b = b""
        for i in range(0, len(self.buffer_black), 50):
            b = self.buffer_black[i:i + 50] + b
        return b

    def test_red(self):
        b = b""
        for i in range(0, len(self.buffer_red), 50):
            b = self.buffer_red[i:i + 50] + b
        return b



    def Sleep(self):
        self.send_command(0X50) 
        self.send_data(0xf7)     
        
        self.send_command(0X02)  
        self.ReadBusy()          
        self.send_command(0X07)  
        self.send_data(0xA5)
    



#example
###
#import epaper4in2
#epd = epaper4in2.EPD_4in2_B()
#epd.Clear()
#epd.imageblack.fill(1)
#epd.imageblack.line(0,0,400,300,0)
#
#epd.display(epd.test_blk(),None)
####

############################################
# str rotation                             #
#                                          #
############################################

#import epaper4in2
#import newframebuf
#epd = epaper4in2.EPD_4in2_B()
#w = 300
#h = 400
#buf = bytearray(w * h // 8)  
#fb = newframebuf.FrameBuffer(buf, h, w, newframebuf.MHMSB)# newframebuf.MHMSB  shoud be changed by the different kind of screen.
#fb.rotation = 3  
#fb.fill(1)
#fb.text("test",0,0,0,size = 5)
#epd.buffer_black = buf
#epd.display(epd.test_blk(),None)
####################################################
#if want to set different ratation in the same time
#can make two separate frame block to use it
#example
#epd.imagered.fill(0)
#epd.imagered.text("test",0,0,1)
#epd.display(None,epd.test_red())
####################################################
buf = bytearray(w * h // 8)  
fb = newframebuf.FrameBuffer(buf, h, w, newframebuf.MHMSB)# newframebuf.MHMSB  shoud be changed by the different kind of screen.
fb.rotation = 3  
fb.fill(1)
fb.text("test",0,0,0,size = 5)