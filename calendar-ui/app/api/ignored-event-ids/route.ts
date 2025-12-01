import { NextRequest, NextResponse } from 'next/server'
import { execSync } from 'child_process'
import path from 'path'

export async function GET() {
  try {
    const parentDir = path.resolve(process.cwd(), '..')
    const scriptPath = path.join(parentDir, 'manage_ignored_event_ids.py')
    const command = `PYTHONPATH="${parentDir}" python3 "${scriptPath}" list`
    
    const output = execSync(command, { 
      encoding: 'utf-8', 
      cwd: parentDir,
      shell: '/bin/bash'
    })
    const ignored = JSON.parse(output)
    
    return NextResponse.json(ignored)
  } catch (error: any) {
    console.error('Error fetching ignored event IDs:', error)
    return NextResponse.json(
      { error: 'Failed to fetch ignored event IDs', details: error.message },
      { status: 500 }
    )
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { event_id, subject, start_time, reason } = body
    
    const parentDir = path.resolve(process.cwd(), '..')
    const scriptPath = path.join(parentDir, 'manage_ignored_event_ids.py')
    
    // Escape quotes for shell command
    const safeSubject = (subject || '').replace(/"/g, '\\"')
    const command = `PYTHONPATH="${parentDir}" python3 "${scriptPath}" add "${event_id}" "${safeSubject}" "${start_time || ''}" "${reason || 'User ignored'}"`
    
    execSync(command, { 
      encoding: 'utf-8', 
      cwd: parentDir,
      shell: '/bin/bash'
    })
    
    return NextResponse.json({ success: true })
  } catch (error: any) {
    console.error('Error adding ignored event ID:', error)
    return NextResponse.json(
      { error: 'Failed to add ignored event ID', details: error.message },
      { status: 500 }
    )
  }
}

export async function DELETE(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const event_id = searchParams.get('event_id')
    
    if (!event_id) {
      return NextResponse.json(
        { error: 'event_id is required' },
        { status: 400 }
      )
    }
    
    const parentDir = path.resolve(process.cwd(), '..')
    const scriptPath = path.join(parentDir, 'manage_ignored_event_ids.py')
    const command = `PYTHONPATH="${parentDir}" python3 "${scriptPath}" remove "${event_id}"`
    
    execSync(command, { 
      encoding: 'utf-8', 
      cwd: parentDir,
      shell: '/bin/bash'
    })
    
    return NextResponse.json({ success: true })
  } catch (error: any) {
    console.error('Error removing ignored event ID:', error)
    return NextResponse.json(
      { error: 'Failed to remove ignored event ID', details: error.message },
      { status: 500 }
    )
  }
}

