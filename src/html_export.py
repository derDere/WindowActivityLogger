"""
HTML export generator for creating self-contained activity reports.
"""
from datetime import datetime, timedelta
import math
from typing import List, Tuple

from db_manager import DatabaseManager


class HTMLExportGenerator:
    def __init__(self, db_manager: DatabaseManager):
        """Initialize the HTML export generator."""
        self._db_manager = db_manager

    def generate_report(self, start_time: datetime, end_time: datetime) -> str:
        """Generate a complete HTML report for the specified time range.

        Args:
            start_time: Start of the reporting period
            end_time: End of the reporting period

        Returns:
            A self-contained HTML report as a string
        """
        # Get data
        project_data = self._db_manager.get_project_summary(start_time, end_time)
        title_data = self._db_manager.get_title_summary(start_time, end_time)

        # Format project data for chart
        chart_data = [(name, duration) for _, name, duration in project_data]

        # Build HTML
        return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Activity Report {start_time.strftime('%Y-%m-%d')} to {end_time.strftime('%Y-%m-%d')}</title>
    <style>
{self._get_css_styles()}
    </style>
</head>
<body>
    <div class="container">
        <h1>Activity Report</h1>
        <p class="period">Period: {start_time.strftime('%Y-%m-%d %H:%M')} to {end_time.strftime('%Y-%m-%d %H:%M')}</p>
        
        <div class="chart-container">
            <h2>Project Distribution</h2>
            {self._generate_project_chart(chart_data)}
        </div>

        <div class="table-container">
            <h2>Project Summary</h2>
            {self._generate_project_table(project_data)}
        </div>

        <div class="table-container">
            <h2>Window Title Summary</h2>
            {self._generate_title_table(title_data)}
        </div>
    </div>
</body>
</html>"""

    def _generate_project_chart(self, project_data: List[Tuple[str, float]]) -> str:
        """Generate SVG pie chart for project distribution.
        
        Args:
            project_data: List of (project_name, duration) tuples
            
        Returns:
            SVG pie chart as string, shows empty circle with message if no data
        """
        # Size and position constants
        size = 400
        center = size / 2
        radius = (size / 2) * 0.8  # Leave room for labels
        
        # Start SVG
        svg = f'<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}">\n'
        
        # Add group for centering
        svg += f'<g transform="translate({center},{center})">\n'
        
        if not project_data:
            # Draw empty circle
            svg += f'  <circle r="{radius}" fill="none" stroke="#ddd" stroke-width="2"/>\n'
            # Add "No data available" text
            svg += '  <text text-anchor="middle" alignment-baseline="middle" '
            svg += 'font-size="16" fill="#666" font-style="italic">No data available</text>\n'
            svg += '</g>\n'
            svg += '</svg>'
            return svg
        
        # Calculate total for percentages
        total = sum(duration for _, duration in project_data)
        
        # Track current angle and colors
        current_angle = 0
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEEAD', 
                 '#D4A5A5', '#9DE0AD', '#FF9999', '#45B7D1', '#E9D985']
        
        # Generate slices
        for i, (name, duration) in enumerate(project_data):
            percentage = (duration / total) * 100
            angle = (duration / total) * 2 * math.pi
            
            # Calculate coordinates
            start_x = radius * math.sin(current_angle)
            start_y = -radius * math.cos(current_angle)
            end_x = radius * math.sin(current_angle + angle)
            end_y = -radius * math.cos(current_angle + angle)
            
            # Large arc flag is 1 if angle > π
            large_arc = 1 if angle > math.pi else 0
            
            # Add pie slice
            color = colors[i % len(colors)]
            svg += f'  <path d="M 0 0 L {start_x} {start_y} A {radius} {radius} 0 {large_arc} 1 {end_x} {end_y} Z" '
            svg += f'fill="{color}" stroke="white" stroke-width="1">\n'
            svg += f'    <title>{name}: {self._format_duration(duration)} ({percentage:.1f}%)</title>\n'
            svg += '  </path>\n'
            
            # Add label
            label_angle = current_angle + (angle / 2)
            label_radius = radius * 1.1
            label_x = label_radius * math.sin(label_angle)
            label_y = -label_radius * math.cos(label_angle)
            
            # Only show label if slice is big enough
            if percentage >= 5:
                svg += f'  <text x="{label_x}" y="{label_y}" text-anchor="middle" '
                svg += f'alignment-baseline="middle" class="chart-label">{percentage:.1f}%</text>\n'
            
            current_angle += angle
        
        svg += '</g>\n'
        
        # Add legend
        legend_y = size - 60
        legend_x = 10
        svg += '<g class="legend">\n'
        for i, (name, duration) in enumerate(project_data):
            percentage = (duration / total) * 100
            color = colors[i % len(colors)]
            y = legend_y + (i * 20)
            svg += f'  <rect x="{legend_x}" y="{y}" width="15" height="15" fill="{color}"/>\n'
            svg += f'  <text x="{legend_x + 25}" y="{y + 12}">{name} ({percentage:.1f}%)</text>\n'
        svg += '</g>\n'
        
        svg += '</svg>'
        return svg

    def _generate_project_table(self, project_data: List[Tuple[int, str, float]]) -> str:
        """Generate HTML table for project summary."""
        if not project_data:
            return '<p class="no-data">No data available</p>'

        html = '<table>\n<thead>\n<tr><th>Project</th><th>Time</th></tr>\n</thead>\n<tbody>\n'
        
        for _, name, duration in project_data:
            html += f'<tr><td>{name}</td><td>{self._format_duration(duration)}</td></tr>\n'
            
        html += '</tbody>\n</table>'
        return html

    def _generate_title_table(self, title_data: List[Tuple[str, float]]) -> str:
        """Generate HTML table for title summary."""
        if not title_data:
            return '<p class="no-data">No data available</p>'

        html = '<table>\n<thead>\n<tr><th>Window Title</th><th>Time</th></tr>\n</thead>\n<tbody>\n'
        
        for title, duration, _ in title_data:
            html += f'<tr><td>{title}</td><td>{self._format_duration(duration)}</td></tr>\n'
            
        html += '</tbody>\n</table>'
        return html

    def _get_css_styles(self) -> str:
        """Get CSS styles for the report."""
        return """
            body {
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                line-height: 1.6;
                margin: 0;
                padding: 20px;
                background: #f5f5f5;
                color: #333;
            }
            
            .container {
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                padding: 30px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            
            h1 {
                color: #2c3e50;
                margin-top: 0;
                border-bottom: 2px solid #eee;
                padding-bottom: 10px;
            }
            
            h2 {
                color: #34495e;
                margin-top: 30px;
            }
            
            .period {
                color: #666;
                font-style: italic;
            }
            
            .chart-container {
                margin: 30px 0;
                text-align: center;
            }
            
            .chart-label {
                font-size: 12px;
                fill: #666;
            }
            
            .legend text {
                font-size: 12px;
                fill: #666;
            }
            
            table {
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
                background: white;
            }
            
            th, td {
                text-align: left;
                padding: 12px;
                border-bottom: 1px solid #ddd;
            }
            
            th {
                background: #f8f9fa;
                color: #2c3e50;
                font-weight: 600;
            }
            
            tr:hover {
                background: #f8f9fa;
            }
            
            td:last-child, th:last-child {
                text-align: right;
            }
            
            .no-data {
                color: #666;
                font-style: italic;
                text-align: center;
                padding: 20px;
            }
        """

    def _format_duration(self, duration: float) -> str:
        """Format duration to human-readable string.

        Args:
            duration: Time duration in seconds

        Returns:
            Formatted string like "2h 15m" or "45m 30s"
        """
        hours = int(duration // 3600)
        minutes = int((duration % 3600) // 60)
        seconds = int(duration % 60)

        if hours > 0:
            return f"{hours}h {minutes}m"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"
