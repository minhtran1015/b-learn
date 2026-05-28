import { CalendarDays, ChevronLeft, ChevronRight, Clock3, MapPin, Plus } from 'lucide-react';
import PageHeader from '../components/PageHeader.jsx';
import { calendarEvents } from '../data/mockData.js';

const monthLabel = 'Tháng 6, 2026';
const weekDays = ['T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'CN'];
const days = Array.from({ length: 35 }, (_, index) => {
  const dayNumber = index + 1;
  return dayNumber <= 30 ? dayNumber : null;
});

function eventsForDay(day) {
  if (!day) return [];
  const dayKey = String(day).padStart(2, '0');
  return calendarEvents.filter((event) => event.date === `2026-06-${dayKey}`);
}

export default function CalendarPage() {
  const upcomingEvents = calendarEvents.filter((event) => event.date >= '2026-05-28');

  return (
    <div className="page-stack">
      <PageHeader
        eyebrow="Lịch học tập"
        title="Lịch và deadline"
        description="Theo dõi lịch học, bài kiểm tra, workshop và hạn nộp trên cùng một bảng lịch."
        action={<button className="button primary"><Plus size={18} />Thêm nhắc lịch</button>}
      />

      <section className="calendar-layout">
        <div className="calendar-board">
          <div className="calendar-toolbar">
            <div>
              <span>Lịch cá nhân</span>
              <h2>{monthLabel}</h2>
            </div>
            <div className="calendar-controls">
              <button aria-label="Tháng trước"><ChevronLeft size={18} /></button>
              <button>Hôm nay</button>
              <button aria-label="Tháng sau"><ChevronRight size={18} /></button>
            </div>
          </div>

          <div className="calendar-weekdays">
            {weekDays.map((day) => <span key={day}>{day}</span>)}
          </div>
          <div className="calendar-grid">
            {days.map((day, index) => {
              const dayEvents = eventsForDay(day);
              return (
                <div key={`${day ?? 'empty'}-${index}`} className={`calendar-cell ${!day ? 'muted' : ''} ${day === 2 ? 'today' : ''}`}>
                  {day && <strong>{day}</strong>}
                  <div className="calendar-events">
                    {dayEvents.slice(0, 2).map((event) => (
                      <span key={event.title} className={`calendar-pill ${event.status}`}>
                        {event.time} {event.title}
                      </span>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        <aside className="agenda-panel">
          <div className="section-title">
            <h2>Sắp tới</h2>
            <CalendarDays size={20} />
          </div>
          <div className="agenda-list">
            {upcomingEvents.map((event) => (
              <article key={`${event.date}-${event.title}`} className={`agenda-item ${event.status}`}>
                <div className="agenda-date">
                  <strong>{event.date.slice(-2)}</strong>
                  <span>{event.date.slice(5, 7)}</span>
                </div>
                <div>
                  <small>{event.type}</small>
                  <h3>{event.title}</h3>
                  <p>{event.course}</p>
                  <div className="meta-line">
                    <span><Clock3 size={15} />{event.time}</span>
                    {event.location && <span><MapPin size={15} />{event.location}</span>}
                  </div>
                </div>
              </article>
            ))}
          </div>
        </aside>
      </section>
    </div>
  );
}
