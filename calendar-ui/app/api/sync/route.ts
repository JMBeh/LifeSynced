import { NextResponse } from 'next/server'
import { execSync } from 'child_process'
import path from 'path'

export async function POST() {
  try {
    // Call Python script to sync all calendars
    const parentDir = path.resolve(process.cwd(), '..')
    const scriptPath = path.join(parentDir, 'sync_all_calendars.py')
    
    // Set PYTHONPATH to include parent directory so shared_db can be imported
    const command = `PYTHONPATH="${parentDir}" python3 "${scriptPath}"`
    
    execSync(command, { 
      encoding: 'utf-8', 
      cwd: parentDir,
      shell: '/bin/bash'
    })
    
    return NextResponse.json({ success: true })
  } catch (error: any) {
    console.error('Error syncing calendars:', error)
    return NextResponse.json(
      { error: 'Sync failed', details: error.message },
      { status: 500 }
    )
  }
}

