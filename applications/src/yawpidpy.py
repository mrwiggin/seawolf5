import seawolf
import math

thruster_cap = .2

def thruster_log(mv):
    if(math.fabs(mv) < 0.01):
        return 0.0
    return (mv/math.fabs(mv)) * math.log(math.fabs(mv)+1,2)

def in_range(a,x,b): 
    if( x < a ): 
        return a 
    elif( x > b ): 
        return b 
    else: 
        return x 

def dataOut(mv):
    out = in_range(-thruster_cap, thruster_log(mv), thruster_cap)
    seawolf.notify.send("THRUSTER_REQUEST", "Yaw {}".format(out))

def angleError(a1,a2):
    error = a1 - a2

    if( math.fabs(error) > 180):
        if(error>0):
            return (360.0 - math.fabs(error))
        return -(360.0 - math.fabs(error))

    return error

def main():
    seawolf.loadConfig("../conf/seawolf.conf")
    seawolf.init("Yaw PID")

    seawolf.var.subscribe("YawPID.p")
    seawolf.var.subscribe("YawPID.i")
    seawolf.var.subscribe("YawPID.d")
    seawolf.var.subscribe("YawPID.Heading")
    seawolf.var.subscribe("YawPID.Paused")
    seawolf.var.subscribe("SEA.Yaw")

    paused = (seawolf.var.get("YawPID.Paused") != 0.0)
    heading = seawolf.var.get("YawPID.Heading")

    pid = seawolf.PID(0.0, seawolf.var.get("YawPID.p"), seawolf.var.get("YawPID.i"), seawolf.var.get("YawPID.d"))

    dataOut(0.0)

    while(True):
        
        seawolf.var.sync()

        if( seawolf.var.stale("YawPID.p") or seawolf.var.stale("YawPID.i") or seawolf.var.stale("YawPID.d")):
            pid.setCoefficients(seawolf.var.get("YawPID.p"), seawolf.var.get("YawPID.i"), seawolf.var.get("YawPID.d"))
            pid.resetIntegral()

        if( seawolf.var.stale("YawPID.Heading")):
            heading = seawolf.var.get("YawPID.Heading")
            if paused:
                dataOut(0.0)
                seawolf.notify.send("PIDPAUSED", "Yaw")
                pid.pause()

        if( seawolf.var.stale("YawPID.Paused")):
            paused = (seawolf.var.get("YawPID.Paused") != 0.0)
            if paused:
                dataOut(0.0)
                seawolf.notify.send("PIDPAUSED", "Yaw")
                pid.pause()

        if (paused == False):
            mv = pid.update( angleError(heading,yaw))
            dataOut(mv)

    seawolf.close()

if __name__ == "__main__":
     main()
