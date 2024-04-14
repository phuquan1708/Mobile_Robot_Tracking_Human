import cv2 as cv
import numpy as np
import serial # giao tiep ardunio
import time 
# nguong so sanh
CONFIDENCE_THRESHOLD = 0.4 # do tien cay
NMS_THRESHOLD = 0.3
KNOWN_DISTANCE = 202 #cm khoang cach tu camera den nguoi cua anh mau
PERSON_WIDTH = 163 #cm chieu cao that cua ngươi

# mau cho doi tuong
COLORS = [(255,0,0),(255,0,255),(0, 255, 255), (255, 255, 0), (0, 255, 0), (255, 0, 0)]
GREEN =(0,255,0)
BLACK =(0,0,0)
YELLOW =(0,255,255)
PERPEL = (255,0,255)
WHITE = (255,255,255)
FONTS = cv.FONT_HERSHEY_COMPLEX
# doc class tu file txt
class_names = []
with open("classes.txt", "r") as f:
    class_names = [cname.strip() for cname in f.readlines()]
yoloNet = cv.dnn.readNet('yolov4-tiny.weights', 'yolov4-tiny.cfg') #doc file weight
#su dung gpu
yoloNet.setPreferableBackend(cv.dnn.DNN_BACKEND_CUDA)
yoloNet.setPreferableTarget(cv.dnn.DNN_TARGET_CUDA)

model = cv.dnn_DetectionModel(yoloNet)
model.setInputParams(size=(416, 416), scale=1/255, swapRB=True)

# cau hinh 

def object_detector(image):
    classes, scores, boxes = model.detect(image, CONFIDENCE_THRESHOLD, NMS_THRESHOLD)
    # tao tep du lieu doi tương
    data_list = []
    for (classid, score, box) in zip(classes, scores, boxes):
     if classid == 0: # id cua class nguoi la 0 chi phat hien vat the la nguoi
        # mau cho doi tuong
        color = COLORS[int(classid) % len(COLORS)]

        label = "%s : %f" % (class_names[classid[0]], score)
 
        # ve hcn tren lable
        cv.rectangle(image, box, color, 2)

        cv.putText(image, label, (box[0], box[1] - 14), FONTS, 0.5, color, 2)

        # luu du lieu
        # 0: ten class  1: chieu cao cua nguoi trong anh, 2: vi tri ve text , 3 tao do x1 cua box, 4 toa do x2 cua box
      # person class id
        data_list.append([class_names[classid[0]], box[3], (box[0], box[1] - 2),box[0],box[2]])  
        break #ta dung break de chi detect 1 vat the 
    return data_list
# ham tim tieu cu f cua may anh (f la hang so khong doi)
def focal_length_finder (measured_distance, real_width, width_in_rf):
    focal_length = (width_in_rf * measured_distance) / real_width

    return focal_length

# ham tim kc tu camera den nguoi
def distance_finder(focal_length, real_object_width, width_in_frame):
    distance = (real_object_width * focal_length) / width_in_frame
    return distance
# tim chieu cao trong anh tu cac anh mau
# ta doc anh mau va tim f trung binh cua 4 anh khac nhau co kc tu nguoi den camera lan luot(200-240-280-320) cm
# anh mau 1
ref_person_1 = cv.imread('anhmau/image200.png')
person_data_1 = object_detector(ref_person_1)
person_width_in_rf_1 = person_data_1[0][1]
# anh mau 2
ref_person_2 = cv.imread('anhmau/image240.png')
person_data_2 = object_detector(ref_person_2)
person_width_in_rf_2 = person_data_2[0][1]
# anh mau 3
ref_person_3 = cv.imread('anhmau/image280.png')
person_data_3 = object_detector(ref_person_3)
person_width_in_rf_3 = person_data_3[0][1]
# anh mau 4
ref_person_4 = cv.imread('anhmau/image320.png')
person_data_4 = object_detector(ref_person_4)
person_width_in_rf_4 = person_data_4[0][1]


# tim tieu cu f trung binh
focal_person_1 = focal_length_finder(KNOWN_DISTANCE, PERSON_WIDTH, person_width_in_rf_1)
focal_person_2 = focal_length_finder(KNOWN_DISTANCE+40, PERSON_WIDTH, person_width_in_rf_2)
focal_person_3 = focal_length_finder(KNOWN_DISTANCE+40, PERSON_WIDTH, person_width_in_rf_3)
focal_person_4 = focal_length_finder(KNOWN_DISTANCE+40, PERSON_WIDTH, person_width_in_rf_4)
focal_person=(focal_person_1+focal_person_2+focal_person_3+focal_person_4)/4
print(f"tieu cu cua may anh : {focal_person}")
#thiet lap giao tiep ardunio
Arduino = serial.Serial(baudrate=9600, port = 'COM4') # chon cong ket noi la COM 4
huong =0 # co 3 huong 0:dung, 1:lui, 2 tien
speed_motor1 =0 # toc do cua dong co 
speed_motor2 =0 #toc do dong c
speed_lon =140#toc do cua banh lon khi quay
speed_nho =125#toc do cua banh nho khi quay
speed_for_backward =110 #toc do khi di thangq

# doc tu camera 
camera = cv.VideoCapture(0)# neu dung camera cua may tinh chon 0

while True:
    ret, frame = camera.read() # doc anh tu camera

    data = object_detector(frame)
    for d in data:
        if d[0] == 'person':
            Right_Bound = 640-150 #gioi han ben phai neu vuot qua thi ro bot rẽ phai
            Left_Bound =150 #gioi han ben phai neu vuot qua thi ro bot rẽ trai
            box_x1=d[3] # toa do goc tren ben trai cua khung label
            box_x2=d[3]+d[4] # toa do goc tren ben phai cua khung label
            distance = distance_finder(focal_person, PERSON_WIDTH, d[1])
            x, y = d[2]
            cv.rectangle(frame, (x, y - 3), (x + 150, y + 23), BLACK, -1)# ve de viet chu
            cv.putText(frame, f'Distance: {round(distance, 2)} cm', (x + 5, y + 13), FONTS, 0.48, GREEN, 2)
            # dieu khien robot
            if box_x1<Left_Bound and distance >170:# khi nguoi ở ben trai va có kc >170 robot re trai va tien
                 
                Motor1_Speed=speed_nho
                Motor2_Speed=speed_lon
                print("quay trai tien")
                # huong di
                huong=2
                cv.line(frame, (50,65), (170, 65), (BLACK), 15)
                cv.putText(frame, f"quay trai tien", (50,70), FONTS,0.4, (YELLOW),1)
            elif box_x1<Left_Bound and distance >50 and distance<=170:# khi nguoi ở ben trai va có kc <=170 robot re trai va lui
                 
                Motor1_Speed=speed_lon
                Motor2_Speed=speed_nho
                print("quay trai lui")
                # huong di
                huong=1
                cv.line(frame, (50,65), (170, 65), (BLACK), 15)
                cv.putText(frame, f"quay trai lui", (50,70), FONTS,0.4, (YELLOW),1)
            elif box_x2>Right_Bound and distance >50 and distance<=170:# khi nguoi ở ben phai va có kc >170 robot re phai va lui
                 
                Motor1_Speed=speed_nho
                Motor2_Speed=speed_lon
                print("quay phai lui")
                # huong di
                huong=1
                cv.line(frame, (50,65), (170, 65), (BLACK), 15)
                cv.putText(frame, f"quay phai lui", (50,70), FONTS,0.4, (YELLOW),1)  
            elif box_x2>Right_Bound and distance >170:# khi nguoi ở ben phai va có kc >170 robot re phai va tien
                 
                Motor1_Speed=speed_lon
                Motor2_Speed=speed_nho
                print("quay phai tien")
                # quay phai
                huong=2
                cv.line(frame, (50,65), (170, 65), (BLACK), 15)
                cv.putText(frame, f"quay phai tien", (50,70), FONTS,0.4, (GREEN),1)
            elif distance >220: #kc>220 tien
                
                Motor1_Speed=speed_for_backward 
                Motor2_Speed=speed_for_backward 
                #di thang
                huong=2
                cv.line(frame, (50,55), (200, 55), (BLACK), 15)
                cv.putText(frame, f"tien", (50,58), FONTS,0.4, (PERPEL),1)
                print("tien")
            
            elif distance >100 and distance<=170: #kc<=170 lui
                 
                Motor1_Speed=speed_for_backward 
                Motor2_Speed=speed_for_backward 
                # lui
                huong=1
                print("lui")
                cv.line(frame, (50,55), (200, 55), (BLACK), 15)
                cv.putText(frame, f"lui", (50,58), FONTS,0.4, (PERPEL),1)
            elif distance >170 and distance<=220:# 170<kc<=220 dung im
               
                Motor1_Speed=0
                Motor2_Speed=0
                # dung im
                huong=0
                print(data)
                cv.line(frame, (50,55), (200, 55), (BLACK), 15)
                cv.putText(frame, f"dung im", (50,58), FONTS,0.4, (PERPEL),1)    
            else:
                time.sleep(0.5)
                Motor1_Speed=0
                Motor2_Speed=0
                # dung im
                huong=0
                print(data)
                cv.line(frame, (50,55), (200, 55), (BLACK), 15)
                cv.putText(frame, f"dung im", (50,58), FONTS,0.4, (PERPEL),1)
            
            data = f"A{Motor1_Speed}B{Motor2_Speed}D{huong}C{round(distance )}" #vd A180B180D1
            print(data)
            Arduino.write(data.encode())# gui du lieu sang ardunio qua cong COM
            time.sleep(0.002) # thoi gian gui du lieu delay
            Arduino.flushInput()


    cv.line(frame, (150, 80), (150, 480-80), (YELLOW), 2)
    cv.line(frame, (490, 80),(490, 480-80), (YELLOW), 2)
    cv.imshow('Webcam', frame)

    key = cv.waitKey(1)
    if key == ord('q'):# khi an q thoat 
        break
camera.release()
cv.destroyAllWindows()