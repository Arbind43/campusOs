"""
Unit tests for AI Assistant service utilities.

Tests time and day parsing functions used for natural language
timetable management.
"""

import pytest
from app.services.ai_assistant import (
    parse_time_expression,
    parse_day_name,
    calculate_end_time,
)


class TestParseTimeExpression:
    """Test parse_time_expression() function."""
    
    def test_parse_am_time_with_space(self):
        """Test parsing 'X AM' format."""
        assert parse_time_expression("9 AM") == "09:00"
        assert parse_time_expression("12 AM") == "00:00"
        assert parse_time_expression("1 AM") == "01:00"
    
    def test_parse_pm_time_with_space(self):
        """Test parsing 'X PM' format."""
        assert parse_time_expression("2 PM") == "14:00"
        assert parse_time_expression("12 PM") == "12:00"
        assert parse_time_expression("11 PM") == "23:00"
    
    def test_parse_am_time_no_space(self):
        """Test parsing 'XAM' format without space."""
        assert parse_time_expression("9AM") == "09:00"
        assert parse_time_expression("11AM") == "11:00"
    
    def test_parse_pm_time_no_space(self):
        """Test parsing 'XPM' format without space."""
        assert parse_time_expression("2PM") == "14:00"
        assert parse_time_expression("5PM") == "17:00"
    
    def test_parse_am_time_with_minutes(self):
        """Test parsing 'X:MM AM' format."""
        assert parse_time_expression("9:30 AM") == "09:30"
        assert parse_time_expression("11:45 AM") == "11:45"
        assert parse_time_expression("12:00 AM") == "00:00"
    
    def test_parse_pm_time_with_minutes(self):
        """Test parsing 'X:MM PM' format."""
        assert parse_time_expression("2:30 PM") == "14:30"
        assert parse_time_expression("5:15 PM") == "17:15"
        assert parse_time_expression("12:30 PM") == "12:30"
    
    def test_parse_24hour_format(self):
        """Test parsing 'HH:MM' 24-hour format."""
        assert parse_time_expression("09:00") == "09:00"
        assert parse_time_expression("14:30") == "14:30"
        assert parse_time_expression("00:00") == "00:00"
        assert parse_time_expression("23:59") == "23:59"
    
    def test_parse_24hour_single_digit_hour(self):
        """Test parsing single-digit hour in 24-hour format."""
        assert parse_time_expression("9:00") == "09:00"
        assert parse_time_expression("5:30") == "05:30"
    
    def test_parse_4digit_format(self):
        """Test parsing 'HHMM' 4-digit format."""
        assert parse_time_expression("0900") == "09:00"
        assert parse_time_expression("1430") == "14:30"
        assert parse_time_expression("0000") == "00:00"
        assert parse_time_expression("2359") == "23:59"
    
    def test_parse_hour_only(self):
        """Test parsing hour-only format."""
        assert parse_time_expression("9") == "09:00"
        assert parse_time_expression("14") == "14:00"
        assert parse_time_expression("0") == "00:00"
        assert parse_time_expression("23") == "23:00"
    
    def test_parse_case_insensitive(self):
        """Test that AM/PM parsing is case-insensitive."""
        assert parse_time_expression("9 am") == "09:00"
        assert parse_time_expression("9 Am") == "09:00"
        assert parse_time_expression("2 pm") == "14:00"
        assert parse_time_expression("2 Pm") == "14:00"
    
    def test_parse_with_leading_zero(self):
        """Test parsing with leading zero in 12-hour format."""
        assert parse_time_expression("09:00 AM") == "09:00"
        assert parse_time_expression("02:30 PM") == "14:30"
    
    def test_parse_invalid_hour_12hour(self):
        """Test that invalid hours in 12-hour format raise ValueError."""
        with pytest.raises(ValueError, match="Invalid hour"):
            parse_time_expression("13 AM")
        with pytest.raises(ValueError, match="Invalid hour"):
            parse_time_expression("0 PM")
    
    def test_parse_invalid_hour_24hour(self):
        """Test that invalid hours in 24-hour format raise ValueError."""
        with pytest.raises(ValueError, match="Invalid hour"):
            parse_time_expression("24:00")
        with pytest.raises(ValueError, match="Invalid hour"):
            parse_time_expression("25:30")
    
    def test_parse_invalid_minute(self):
        """Test that invalid minutes raise ValueError."""
        with pytest.raises(ValueError, match="Invalid minute"):
            parse_time_expression("9:60 AM")
        with pytest.raises(ValueError, match="Invalid minute"):
            parse_time_expression("14:75")
    
    def test_parse_invalid_format(self):
        """Test that completely invalid formats raise ValueError."""
        with pytest.raises(ValueError, match="Unable to parse"):
            parse_time_expression("invalid")
        with pytest.raises(ValueError, match="Unable to parse"):
            parse_time_expression("25:00 XM")
        with pytest.raises(ValueError, match="Unable to parse"):
            parse_time_expression("abc:def")
    
    def test_parse_empty_string(self):
        """Test that empty string raises ValueError."""
        with pytest.raises(ValueError, match="Invalid time expression"):
            parse_time_expression("")
    
    def test_parse_none(self):
        """Test that None raises ValueError."""
        with pytest.raises(ValueError, match="Invalid time expression"):
            parse_time_expression(None)
    
    def test_parse_with_extra_whitespace(self):
        """Test that extra whitespace is handled."""
        assert parse_time_expression("  9 AM  ") == "09:00"
        assert parse_time_expression("  14:30  ") == "14:30"


class TestParseDayName:
    """Test parse_day_name() function."""
    
    def test_parse_full_lowercase_names(self):
        """Test parsing full day names in lowercase."""
        assert parse_day_name("monday") == "Monday"
        assert parse_day_name("tuesday") == "Tuesday"
        assert parse_day_name("wednesday") == "Wednesday"
        assert parse_day_name("thursday") == "Thursday"
        assert parse_day_name("friday") == "Friday"
        assert parse_day_name("saturday") == "Saturday"
        assert parse_day_name("sunday") == "Sunday"
    
    def test_parse_full_uppercase_names(self):
        """Test parsing full day names in uppercase."""
        assert parse_day_name("MONDAY") == "Monday"
        assert parse_day_name("TUESDAY") == "Tuesday"
        assert parse_day_name("WEDNESDAY") == "Wednesday"
    
    def test_parse_full_mixed_case_names(self):
        """Test parsing full day names in mixed case."""
        assert parse_day_name("Monday") == "Monday"
        assert parse_day_name("TuEsDaY") == "Tuesday"
    
    def test_parse_abbreviations(self):
        """Test parsing common day abbreviations."""
        assert parse_day_name("Mon") == "Monday"
        assert parse_day_name("Tue") == "Tuesday"
        assert parse_day_name("Wed") == "Wednesday"
        assert parse_day_name("Thu") == "Thursday"
        assert parse_day_name("Fri") == "Friday"
        assert parse_day_name("Sat") == "Saturday"
        assert parse_day_name("Sun") == "Sunday"
    
    def test_parse_lowercase_abbreviations(self):
        """Test parsing lowercase abbreviations."""
        assert parse_day_name("mon") == "Monday"
        assert parse_day_name("tue") == "Tuesday"
        assert parse_day_name("wed") == "Wednesday"
    
    def test_parse_uppercase_abbreviations(self):
        """Test parsing uppercase abbreviations."""
        assert parse_day_name("MON") == "Monday"
        assert parse_day_name("TUE") == "Tuesday"
        assert parse_day_name("WED") == "Wednesday"
    
    def test_parse_alternative_abbreviations(self):
        """Test parsing alternative abbreviations."""
        assert parse_day_name("tues") == "Tuesday"
        assert parse_day_name("thur") == "Thursday"
        assert parse_day_name("thurs") == "Thursday"
    
    def test_parse_with_whitespace(self):
        """Test that whitespace is handled."""
        assert parse_day_name("  Monday  ") == "Monday"
        assert parse_day_name("  mon  ") == "Monday"
    
    def test_parse_invalid_day_name(self):
        """Test that invalid day names raise ValueError."""
        with pytest.raises(ValueError, match="Invalid day name"):
            parse_day_name("Notaday")
        with pytest.raises(ValueError, match="Invalid day name"):
            parse_day_name("xyz")
    
    def test_parse_empty_string(self):
        """Test that empty string raises ValueError."""
        with pytest.raises(ValueError, match="Invalid day name"):
            parse_day_name("")
    
    def test_parse_none(self):
        """Test that None raises ValueError."""
        with pytest.raises(ValueError, match="Invalid day name"):
            parse_day_name(None)


class TestCalculateEndTime:
    """Test calculate_end_time() function."""
    
    def test_calculate_default_1hour_duration(self):
        """Test calculating end time with default 1-hour duration."""
        assert calculate_end_time("09:00") == "10:00"
        assert calculate_end_time("14:30") == "15:30"
        assert calculate_end_time("08:45") == "09:45"
    
    def test_calculate_custom_duration(self):
        """Test calculating end time with custom duration."""
        assert calculate_end_time("09:00", 2) == "11:00"
        assert calculate_end_time("14:00", 3) == "17:00"
        assert calculate_end_time("10:30", 1) == "11:30"
    
    def test_calculate_wraps_around_midnight(self):
        """Test that time wraps around midnight correctly."""
        assert calculate_end_time("23:00", 1) == "00:00"
        assert calculate_end_time("23:30", 1) == "00:30"
        assert calculate_end_time("22:00", 3) == "01:00"
    
    def test_calculate_with_leading_zeros(self):
        """Test with times having leading zeros."""
        assert calculate_end_time("09:00") == "10:00"
        assert calculate_end_time("05:15") == "06:15"
    
    def test_calculate_without_leading_zeros(self):
        """Test with times missing leading zeros."""
        assert calculate_end_time("9:00") == "10:00"
        assert calculate_end_time("5:30") == "06:30"
    
    def test_calculate_invalid_format(self):
        """Test that invalid format raises ValueError."""
        with pytest.raises(ValueError, match="HH:MM format"):
            calculate_end_time("9 AM")
        with pytest.raises(ValueError, match="HH:MM format"):
            calculate_end_time("invalid")
    
    def test_calculate_invalid_hour(self):
        """Test that invalid hour raises ValueError."""
        with pytest.raises(ValueError, match="Invalid hour"):
            calculate_end_time("24:00")
        with pytest.raises(ValueError, match="Invalid hour"):
            calculate_end_time("25:30")
    
    def test_calculate_invalid_minute(self):
        """Test that invalid minute raises ValueError."""
        with pytest.raises(ValueError, match="Invalid minute"):
            calculate_end_time("09:60")
        with pytest.raises(ValueError, match="Invalid minute"):
            calculate_end_time("14:75")
    
    def test_calculate_empty_string(self):
        """Test that empty string raises ValueError."""
        with pytest.raises(ValueError, match="Invalid start time"):
            calculate_end_time("")
    
    def test_calculate_none(self):
        """Test that None raises ValueError."""
        with pytest.raises(ValueError, match="Invalid start time"):
            calculate_end_time(None)
    
    def test_calculate_with_whitespace(self):
        """Test that whitespace is handled."""
        assert calculate_end_time("  09:00  ") == "10:00"
        assert calculate_end_time("  14:30  ") == "15:30"


class TestTimeParsingIntegration:
    """Integration tests combining multiple time parsing functions."""
    
    def test_parse_and_calculate_workflow(self):
        """Test typical workflow: parse time expression, then calculate end time."""
        # User says "9 AM", we parse it, then calculate end time
        start_time = parse_time_expression("9 AM")
        assert start_time == "09:00"
        
        end_time = calculate_end_time(start_time)
        assert end_time == "10:00"
    
    def test_parse_various_formats_and_calculate(self):
        """Test parsing different formats and calculating end times."""
        # Test various input formats
        test_cases = [
            ("2:30 PM", "14:30", "15:30"),
            ("0900", "09:00", "10:00"),
            ("14:00", "14:00", "15:00"),
            ("5 PM", "17:00", "18:00"),
        ]
        
        for input_time, expected_start, expected_end in test_cases:
            start_time = parse_time_expression(input_time)
            assert start_time == expected_start
            
            end_time = calculate_end_time(start_time)
            assert end_time == expected_end


class TestDayNameIntegration:
    """Integration tests for day name parsing."""
    
    def test_normalize_various_formats(self):
        """Test normalizing various day name formats."""
        test_cases = [
            ("mon", "Monday"),
            ("MONDAY", "Monday"),
            ("Monday", "Monday"),
            ("Tue", "Tuesday"),
            ("wednesday", "Wednesday"),
            ("THU", "Thursday"),
            ("Fri", "Friday"),
        ]
        
        for input_day, expected_day in test_cases:
            result = parse_day_name(input_day)
            assert result == expected_day
