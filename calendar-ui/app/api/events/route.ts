import { NextResponse } from 'next/server'
import { execSync } from 'child_process'
import path from 'path'

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url)
    const daysAhead = parseInt(searchParams.get('daysAhead') || '30', 10)
    
    // Call Python script to query database
    // process.cwd() is the calendar-ui directory in Next.js
    const scriptPath = path.join(process.cwd(), 'query_db_api.py')
    const parentDir = path.join(process.cwd(), '..')
    
    // Set PYTHONPATH to include parent directory so shared_db can be imported
    const command = `PYTHONPATH="${parentDir}" python3 "${scriptPath}" ${daysAhead}`
    
    const output = execSync(command, { 
      encoding: 'utf-8', 
      cwd: process.cwd(),
      shell: '/bin/bash'
    })
    const events = JSON.parse(output)
    
    return NextResponse.json(events)
  } catch (error: any) {
    console.error('Error fetching events:', error)
    return NextResponse.json(
      { error: 'Failed to fetch events', details: error.message },
      { status: 500 }
    )
  }
}

