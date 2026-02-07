# Appendix B: Data Type Reference

This appendix provides a detailed reference for all 13 data types supported by MSD.

## B.1 Type Overview

| Type | Category | Accepts Size | SQL Equivalent |
|------|----------|:------------:|----------------|
| `INT` | Numeric | No | `INTEGER` |
| `BIGINT` | Numeric | No | `BIGINT` |
| `SMALLINT` | Numeric | No | `SMALLINT` |
| `VARCHAR` | String | Yes | `VARCHAR(n)` |
| `CHAR` | String | Yes | `CHAR(n)` |
| `TEXT` | String | No | `TEXT` |
| `BOOLEAN` | Logical | No | `BOOLEAN` |
| `DATE` | Temporal | No | `DATE` |
| `TIME` | Temporal | No | `TIME` |
| `TIMESTAMP` | Temporal | No | `TIMESTAMP` |
| `DECIMAL` | Numeric | Yes | `DECIMAL(p)` |
| `FLOAT` | Numeric | No | `REAL` |
| `DOUBLE` | Numeric | No | `DOUBLE PRECISION` |

## B.2 Numeric Types

### INT

```msd
*id: INT
quantity: INT
```

A standard 32-bit integer. The most common type for primary keys and counters. Range: -2,147,483,648 to 2,147,483,647 in most databases.

### BIGINT

```msd
*transaction_id: BIGINT
file_size: BIGINT
```

A 64-bit integer for values that exceed INT range. Common for auto-incrementing IDs in high-volume systems. Range: approximately -9.2 x 10^18 to 9.2 x 10^18.

### SMALLINT

```msd
age: SMALLINT
priority: SMALLINT
```

A 16-bit integer for small numeric values. Saves storage when the range is known to be small. Range: -32,768 to 32,767.

### DECIMAL

```msd
price: DECIMAL(10)
tax_rate: DECIMAL(5)
```

A fixed-point number with exact precision. The size parameter specifies the number of significant digits. Essential for monetary values where floating-point rounding is unacceptable.

**Size parameter**: Required for meaningful use. `DECIMAL(10)` means up to 10 significant digits.

### FLOAT

```msd
latitude: FLOAT
temperature: FLOAT
```

A single-precision floating-point number (32-bit IEEE 754). Approximately 7 decimal digits of precision. Use for scientific or approximate values where exact precision is not critical.

### DOUBLE

```msd
longitude: DOUBLE
measurement: DOUBLE
```

A double-precision floating-point number (64-bit IEEE 754). Approximately 15 decimal digits of precision. Use when FLOAT does not provide sufficient precision.

## B.3 String Types

### VARCHAR

```msd
name: VARCHAR(255)
email: VARCHAR(320)
country_code: VARCHAR(3)
```

A variable-length character string. The size parameter specifies the maximum number of characters. The most commonly used string type.

**Size parameter**: Strongly recommended. `VARCHAR` without a size may be treated differently by different databases.

### CHAR

```msd
currency_code: CHAR(3)
gender: CHAR(1)
postal_code: CHAR(10)
```

A fixed-length character string. The size parameter specifies the exact number of characters. Values shorter than the specified length are typically padded with spaces.

**Size parameter**: Strongly recommended. Use for codes and identifiers of known, fixed length.

### TEXT

```msd
description: TEXT
biography: TEXT
content: TEXT
```

An unlimited-length character string. No size parameter. Use for large text fields where the maximum length is unknown or very large.

## B.4 Temporal Types

### DATE

```msd
date_of_birth: DATE
hire_date: DATE
```

A calendar date (year, month, day) without a time component. Format depends on the database but is typically `YYYY-MM-DD`.

### TIME

```msd
start_time: TIME
end_time: TIME
```

A time of day (hours, minutes, seconds) without a date component. Format is typically `HH:MM:SS`.

### TIMESTAMP

```msd
created_at: TIMESTAMP
last_login: TIMESTAMP
```

A combined date and time value. The most precise temporal type. Format is typically `YYYY-MM-DD HH:MM:SS`.

## B.5 Logical Types

### BOOLEAN

```msd
is_active: BOOLEAN
has_verified_email: BOOLEAN
```

A true/false value. Some databases store this as a single bit; others use a small integer (0/1).

## B.6 Type Name Case Insensitivity

Type names are case-insensitive in MSD. All of the following are equivalent:

```msd
name: VARCHAR(100)
name: varchar(100)
name: Varchar(100)
name: VARCHAR(100)
```

They are all normalised to `VARCHAR` internally. The canonical uppercase form is what appears in the generated `.merisio` file and in SQL output.

## B.7 Size Parameter Rules

Only three types accept a size parameter:

| Type | Size Meaning | Example |
|------|-------------|---------|
| `VARCHAR` | Maximum character count | `VARCHAR(255)` |
| `CHAR` | Exact character count | `CHAR(3)` |
| `DECIMAL` | Significant digit count | `DECIMAL(10)` |

If a size parameter is provided on a type that does not accept one, the parser emits a warning:

```
schema.msd:3: warning: data type 'INT' does not accept a size parameter
```

The size is still stored but has no effect on SQL generation for that type.

## B.8 Choosing the Right Type

### For Primary Keys

- Use `INT` for most tables
- Use `BIGINT` for tables expected to exceed 2 billion rows
- Use `VARCHAR` for natural keys (email addresses, codes)

### For Names and Labels

- Use `VARCHAR(n)` with an appropriate maximum length
- Use `TEXT` only when the length is truly unbounded

### For Monetary Values

- Always use `DECIMAL(p)` — never `FLOAT` or `DOUBLE`
- Floating-point arithmetic introduces rounding errors

### For Timestamps

- Use `TIMESTAMP` for recording when events occurred
- Use `DATE` for date-only fields (birthdays, hire dates)
- Use `TIME` for recurring schedules (daily start time)

### For Flags

- Use `BOOLEAN` for true/false values
- Avoid using `INT` or `SMALLINT` as boolean surrogates
