import { Button } from "@/components/ui/button"
import { Calendar, Clock, MapPin } from "lucide-react"

export function UpcomingAppointments() {
  const appointments = [
    {
      id: 1,
      doctor: "Dr. Sarah Johnson",
      specialty: "Endocrinologist",
      date: "May 3, 2023",
      time: "10:30 AM",
      location: "Endocrine Specialists of New York",
      address: "123 Medical Plaza, New York, NY 10001",
    },
    {
      id: 2,
      doctor: "Dr. Michael Chen",
      specialty: "Cardiologist",
      date: "May 15, 2023",
      time: "2:00 PM",
      location: "Heart & Vascular Institute",
      address: "456 Cardiology Lane, New York, NY 10002",
    },
  ]

  return (
    <div className="space-y-4">
      {appointments.length === 0 ? (
        <p className="text-sm text-muted-foreground text-center py-4">
          No upcoming appointments. Schedule one with a specialist.
        </p>
      ) : (
        <div className="space-y-4">
          {appointments.map((appointment) => (
            <div key={appointment.id} className="rounded-lg border p-4">
              <div className="flex justify-between items-start">
                <h3 className="font-medium">{appointment.doctor}</h3>
                <Button variant="outline" size="sm">
                  Reschedule
                </Button>
              </div>
              <p className="text-sm text-muted-foreground">{appointment.specialty}</p>
              <div className="mt-4 space-y-2">
                <div className="flex items-center text-sm">
                  <Calendar className="h-4 w-4 mr-2 text-muted-foreground" />
                  <span>{appointment.date}</span>
                </div>
                <div className="flex items-center text-sm">
                  <Clock className="h-4 w-4 mr-2 text-muted-foreground" />
                  <span>{appointment.time}</span>
                </div>
                <div className="flex items-center text-sm">
                  <MapPin className="h-4 w-4 mr-2 text-muted-foreground" />
                  <div>
                    <div>{appointment.location}</div>
                    <div className="text-xs text-muted-foreground">{appointment.address}</div>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
      <div className="flex justify-center">
        <Button variant="outline" className="w-full">
          Schedule New Appointment
        </Button>
      </div>
    </div>
  )
}
