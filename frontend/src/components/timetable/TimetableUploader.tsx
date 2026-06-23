"use client";

import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { uploadTimetable, confirmTimetable, UploadResponse, TimetableEntry } from "@/lib/timetable-api";
import { getErrorMessage } from "@/lib/api";
import { Upload, AlertCircle, CheckCircle, Plus, Trash2 } from "lucide-react";

interface TimetableUploaderProps {
  onSuccess?: (entries: TimetableEntry[]) => void;
  onCancel?: () => void;
  initialEntries?: TimetableEntry[];
}

export default function TimetableUploader({ onSuccess, onCancel, initialEntries }: TimetableUploaderProps) {
  const [uploading, setUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [preview, setPreview] = useState<string | null>(null);
  const [response, setResponse] = useState<UploadResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [editingEntries, setEditingEntries] = useState<TimetableEntry[]>([]);
  const [showManualAdd, setShowManualAdd] = useState(false);
  const [manualEntry, setManualEntry] = useState({
    subject: "",
    day_of_week: "Monday",
    start_time: "09:00",
    end_time: "10:00",
    room: "",
    faculty_name: "",
  });
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Load initial entries if provided (for edit mode)
  useEffect(() => {
    if (initialEntries && initialEntries.length > 0) {
      setEditingEntries(initialEntries);
      setShowManualAdd(false);
      setResponse({
        success: true,
        message: "Editing existing timetable",
        entries: initialEntries,
        extracted_text: "",
        entries_created: initialEntries.length,
        errors: [],
      });
    }
  }, [initialEntries]);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(e.type === "dragenter" || e.type === "dragover");
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    const files = e.dataTransfer.files;
    if (files && files[0]) {
      await handleFile(files[0]);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0]);
    }
  };

  const handleFile = async (file: File) => {
    if (!["image/jpeg", "image/png"].includes(file.type)) {
      setError("Please upload a JPEG or PNG image");
      setPreview(null);
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      setError("File size must be less than 10 MB");
      setPreview(null);
      return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
      setPreview(e.target?.result as string);
    };
    reader.readAsDataURL(file);

    await uploadFile(file);
  };

  const uploadFile = async (file: File) => {
    setUploading(true);
    setError(null);
    setResponse(null);

    try {
      const result = await uploadTimetable(file);
      setResponse(result);
      setEditingEntries(result.entries);

      // If no entries found, allow manual entry
      if (result.entries.length === 0) {
        setShowManualAdd(true);
        setError("No timetable entries found in image. Please add entries manually below.");
      } else if (!result.success) {
        setError(result.message || "Upload failed");
      }
    } catch (err) {
      setError(`Upload error: ${getErrorMessage(err)}`);
    } finally {
      setUploading(false);
    }
  };

  const handleEditEntry = (index: number, field: string, value: string) => {
    const updated = [...editingEntries];
    updated[index] = { ...updated[index], [field]: value };
    setEditingEntries(updated);
  };

  const handleDeleteEntry = (index: number) => {
    setEditingEntries(editingEntries.filter((_, i) => i !== index));
  };

  const handleAddManualEntry = () => {
    if (!manualEntry.subject || !manualEntry.day_of_week) {
      setError("Please fill in Subject and Day of Week");
      return;
    }

    const newEntry: TimetableEntry = {
      id: Math.floor(Math.random() * -1000000),
      ...manualEntry,
      department_id: "",
      semester: 1,
      created_at: new Date().toISOString(),
    };

    setEditingEntries([...editingEntries, newEntry]);
    setManualEntry({
      subject: "",
      day_of_week: "Monday",
      start_time: "09:00",
      end_time: "10:00",
      room: "",
      faculty_name: "",
    });
    setShowManualAdd(false);
  };

  const handleConfirmAndSubmit = async () => {
    if (editingEntries.length === 0) {
      setError("Please add at least one timetable entry");
      return;
    }

    setUploading(true);
    setError(null);

    try {
      // Call the confirm API to save entries to database
      const result = await confirmTimetable(editingEntries);
      
      if (result.success) {
        // Clear the form and notify parent
        onSuccess?.(result.entries);
        setEditingEntries([]);
        setPreview(null);
        setResponse(null);
      } else {
        setError(result.message || "Failed to save timetable");
      }
    } catch (err) {
      setError(`Save error: ${getErrorMessage(err)}`);
    } finally {
      setUploading(false);
    }
  };

  const days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

  return (
    <div className="space-y-4">
      {editingEntries.length === 0 && !response && (
        <>
          <Card
            className={`border-2 border-dashed transition ${
              dragActive ? "border-primary bg-primary/5" : "border-muted-foreground/30 hover:border-primary"
            }`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            <CardContent className="p-6">
              <div className="flex flex-col items-center justify-center gap-4">
                <Upload className="h-8 w-8 text-muted-foreground" />
                <div className="text-center">
                  <p className="font-medium">Drag and drop your timetable image</p>
                  <p className="text-sm text-muted-foreground">or click to select (JPEG/PNG, max 10 MB)</p>
                </div>
                <Button variant="outline" onClick={() => fileInputRef.current?.click()} disabled={uploading}>
                  {uploading ? "Processing..." : "Select Image"}
                </Button>
                <input ref={fileInputRef} type="file" accept="image/jpeg,image/png" onChange={handleFileSelect} className="hidden" />
              </div>
            </CardContent>
          </Card>

          <div className="text-center text-sm text-muted-foreground">
            <p>or</p>
          </div>

          <Button 
            variant="outline" 
            onClick={() => { 
              setShowManualAdd(true); 
              setResponse({ 
                success: true, 
                message: "Manual entry mode - add entries below", 
                entries: [], 
                extracted_text: "", 
                entries_created: 0, 
                errors: [] 
              }); 
              setEditingEntries([]); // Initialize as empty but trigger the UI
            }} 
            className="w-full"
          >
            <Plus className="h-4 w-4 mr-2" />
            Create Timetable Manually (Skip OCR)
          </Button>
        </>
      )}

      {preview && editingEntries.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">📸 Source Image</CardTitle>
          </CardHeader>
          <CardContent>
            <img src={preview} alt="Timetable preview" className="max-h-48 w-auto rounded border" />
          </CardContent>
        </Card>
      )}

      {error && (
        <div className="flex gap-2 rounded-lg bg-red-50 p-3 text-sm text-red-700 dark:bg-red-900/20 dark:text-red-400">
          <AlertCircle className="h-4 w-4 flex-shrink-0 mt-0.5" />
          <div>{error}</div>
        </div>
      )}

      {response && (editingEntries.length > 0 || showManualAdd) && (
        <Card className={response.success ? "border-green-200 dark:border-green-800" : "border-amber-200 dark:border-amber-800"}>
          <CardHeader>
            <div className="flex items-center gap-2">
              {response.success ? (
                <>
                  <CheckCircle className="h-5 w-5 text-green-600" />
                  <CardTitle className="text-base">OCR Extraction Complete</CardTitle>
                </>
              ) : (
                <>
                  <AlertCircle className="h-5 w-5 text-amber-600" />
                  <CardTitle className="text-base">Partial Extraction</CardTitle>
                </>
              )}
            </div>
            <CardDescription>{response.message}</CardDescription>
          </CardHeader>
          {response.extracted_text && (
            <CardContent>
              <p className="text-sm font-medium mb-2">Extracted Text:</p>
              <p className="text-sm text-muted-foreground whitespace-pre-wrap max-h-24 overflow-y-auto rounded bg-muted p-2">
                {response.extracted_text}
              </p>
            </CardContent>
          )}
        </Card>
      )}

      {(editingEntries.length > 0 || (response && showManualAdd)) && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold">
              {editingEntries.length > 0 ? '📋 Edit Timetable Entries' : '📝 Create Timetable Entries'}
            </h3>
            {editingEntries.length > 0 && (
              <span className="text-sm text-muted-foreground">{editingEntries.length} entries</span>
            )}
          </div>

          {editingEntries.length === 0 && showManualAdd && (
            <div className="flex gap-2 rounded-lg bg-blue-50 p-3 text-sm text-blue-700 dark:bg-blue-900/20 dark:text-blue-400">
              <AlertCircle className="h-4 w-4 flex-shrink-0 mt-0.5" />
              <div>Add your first timetable entry using the form below. You can add multiple entries before saving.</div>
            </div>
          )}

          {editingEntries.length > 0 && (
            <div className="space-y-3">
              {editingEntries.map((entry, idx) => (
              <Card key={entry.id} className="border">
                <CardContent className="p-4">
                  <div className="space-y-3">
                    <div>
                      <Label className="text-xs font-semibold text-muted-foreground">Subject *</Label>
                      <Input
                        value={entry.subject}
                        onChange={(e) => handleEditEntry(idx, "subject", e.target.value)}
                        placeholder="e.g., Mathematics 101"
                        className="mt-1"
                      />
                    </div>

                    <div className="grid grid-cols-3 gap-2">
                      <div>
                        <Label className="text-xs font-semibold text-muted-foreground">Day *</Label>
                        <select
                          value={entry.day_of_week}
                          onChange={(e) => handleEditEntry(idx, "day_of_week", e.target.value)}
                          className="w-full mt-1 rounded border border-input px-3 py-2 text-sm"
                        >
                          {days.map((day) => (
                            <option key={day} value={day}>
                              {day}
                            </option>
                          ))}
                        </select>
                      </div>
                      <div>
                        <Label className="text-xs font-semibold text-muted-foreground">Start Time</Label>
                        <Input
                          type="time"
                          value={entry.start_time}
                          onChange={(e) => handleEditEntry(idx, "start_time", e.target.value)}
                          className="mt-1"
                        />
                      </div>
                      <div>
                        <Label className="text-xs font-semibold text-muted-foreground">End Time</Label>
                        <Input
                          type="time"
                          value={entry.end_time}
                          onChange={(e) => handleEditEntry(idx, "end_time", e.target.value)}
                          className="mt-1"
                        />
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-2">
                      <div>
                        <Label className="text-xs font-semibold text-muted-foreground">Room</Label>
                        <Input
                          value={entry.room || ""}
                          onChange={(e) => handleEditEntry(idx, "room", e.target.value)}
                          placeholder="e.g., Room 201"
                          className="mt-1"
                        />
                      </div>
                      <div>
                        <Label className="text-xs font-semibold text-muted-foreground">Faculty</Label>
                        <Input
                          value={entry.faculty_name || ""}
                          onChange={(e) => handleEditEntry(idx, "faculty_name", e.target.value)}
                          placeholder="e.g., Dr. Smith"
                          className="mt-1"
                        />
                      </div>
                    </div>

                    <div className="flex justify-end pt-2 border-t">
                      <Button variant="destructive" size="sm" onClick={() => handleDeleteEntry(idx)}>
                        <Trash2 className="h-4 w-4 mr-1" />
                        Remove
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
          )}

          {editingEntries.length > 0 && !showManualAdd ? (
            <Button variant="outline" onClick={() => setShowManualAdd(true)} className="w-full">
              <Plus className="h-4 w-4 mr-2" />
              Add Manual Entry
            </Button>
          ) : (
            <Card className="border-dashed">
              <CardContent className="p-4">
                <h4 className="font-semibold mb-3">Add New Entry Manually</h4>
                <div className="space-y-3">
                  <div>
                    <Label className="text-xs font-semibold">Subject *</Label>
                    <Input
                      value={manualEntry.subject}
                      onChange={(e) => setManualEntry({ ...manualEntry, subject: e.target.value })}
                      placeholder="e.g., Physics 201"
                      className="mt-1"
                    />
                  </div>

                  <div className="grid grid-cols-3 gap-2">
                    <div>
                      <Label className="text-xs font-semibold">Day *</Label>
                      <select
                        value={manualEntry.day_of_week}
                        onChange={(e) => setManualEntry({ ...manualEntry, day_of_week: e.target.value })}
                        className="w-full mt-1 rounded border border-input px-3 py-2 text-sm"
                      >
                        {days.map((day) => (
                          <option key={day} value={day}>
                            {day}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <Label className="text-xs font-semibold">Start Time</Label>
                      <Input
                        type="time"
                        value={manualEntry.start_time}
                        onChange={(e) => setManualEntry({ ...manualEntry, start_time: e.target.value })}
                        className="mt-1"
                      />
                    </div>
                    <div>
                      <Label className="text-xs font-semibold">End Time</Label>
                      <Input
                        type="time"
                        value={manualEntry.end_time}
                        onChange={(e) => setManualEntry({ ...manualEntry, end_time: e.target.value })}
                        className="mt-1"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <Label className="text-xs font-semibold">Room</Label>
                      <Input
                        value={manualEntry.room}
                        onChange={(e) => setManualEntry({ ...manualEntry, room: e.target.value })}
                        placeholder="Optional"
                        className="mt-1"
                      />
                    </div>
                    <div>
                      <Label className="text-xs font-semibold">Faculty</Label>
                      <Input
                        value={manualEntry.faculty_name}
                        onChange={(e) => setManualEntry({ ...manualEntry, faculty_name: e.target.value })}
                        placeholder="Optional"
                        className="mt-1"
                      />
                    </div>
                  </div>

                  <div className="flex gap-2 pt-2">
                    <Button onClick={handleAddManualEntry} className="flex-1">
                      <Plus className="h-4 w-4 mr-1" />
                      Add Entry
                    </Button>
                    <Button variant="outline" onClick={() => setShowManualAdd(false)}>
                      Cancel
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          <div className="flex gap-2 pt-4 border-t">
            <Button
              onClick={() => {
                if (onCancel) {
                  onCancel();
                } else {
                  setEditingEntries([]);
                  setPreview(null);
                  setResponse(null);
                }
              }}
              variant="outline"
              className="flex-1"
            >
              Cancel
            </Button>
            <Button onClick={handleConfirmAndSubmit} className="flex-1" disabled={uploading}>
              <CheckCircle className="h-4 w-4 mr-2" />
              {uploading ? "Saving..." : "Confirm & Save Timetable"}
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
