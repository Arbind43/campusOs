"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { TimetableEntry } from "@/lib/timetable-api";
import { Pencil } from "lucide-react";

interface TimetableDisplayProps {
  entries: TimetableEntry[];
  isAdmin?: boolean;
  onEdit?: (entries: TimetableEntry[]) => void;
}

const DAYS_ORDER = [
  "Monday",
  "Tuesday",
  "Wednesday",
  "Thursday",
  "Friday",
  "Saturday",
  "Sunday",
];

export default function TimetableDisplay({ entries, isAdmin = false, onEdit }: TimetableDisplayProps) {
  if (!entries || entries.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Your Timetable</CardTitle>
          <CardDescription>No classes found. Upload a timetable image to get started.</CardDescription>
        </CardHeader>
      </Card>
    );
  }

  // Group entries by day
  const entriesByDay = DAYS_ORDER.reduce(
    (acc, day) => {
      acc[day] = entries
        .filter((e) => e.day_of_week === day)
        .sort(
          (a, b) =>
            new Date(`2000-01-01 ${a.start_time}`).getTime() -
            new Date(`2000-01-01 ${b.start_time}`).getTime()
        );
      return acc;
    },
    {} as Record<string, TimetableEntry[]>
  );

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Your Timetable</CardTitle>
            <CardDescription>{entries.length} classes scheduled</CardDescription>
          </div>
          {isAdmin && onEdit && (
            <Button variant="outline" size="sm" onClick={() => onEdit(entries)}>
              <Pencil className="h-4 w-4 mr-2" />
              Edit Timetable
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          {DAYS_ORDER.map((day) => {
            const dayEntries = entriesByDay[day];
            if (dayEntries.length === 0) return null;

            return (
              <div key={day}>
                <h3 className="font-semibold mb-3 text-sm">{day}</h3>
                <div className="space-y-2">
                  {dayEntries.map((entry) => (
                    <div
                      key={entry.id}
                      className="rounded-lg border border-muted bg-card p-3 hover:bg-muted/50 transition"
                    >
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1 min-w-0">
                          <p className="font-medium text-sm leading-tight">
                            {entry.subject}
                          </p>
                          <p className="text-xs text-muted-foreground mt-1">
                            {entry.start_time} – {entry.end_time}
                          </p>
                          <div className="flex gap-2 mt-2 flex-wrap">
                            {entry.room && (
                              <span className="inline-block text-xs bg-muted px-2 py-1 rounded">
                                {entry.room}
                              </span>
                            )}
                            {entry.faculty_name && (
                              <span className="inline-block text-xs bg-muted px-2 py-1 rounded">
                                {entry.faculty_name}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
