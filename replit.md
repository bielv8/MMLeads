# Overview

This is a real estate lead management system built with Flask that integrates with Meta (Facebook) Lead Ads API to automatically capture and distribute leads to real estate brokers. The system provides role-based access control with admin and broker roles, automated lead distribution, and comprehensive reporting capabilities.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Backend Framework
- **Flask**: Python web framework serving as the main application server
- **SQLAlchemy**: ORM for database operations with declarative base model
- **Flask-JWT-Extended**: JWT token management for API authentication
- **APScheduler**: Background task scheduler for periodic Meta API synchronization

## Authentication & Authorization
- **Session-based authentication**: Primary authentication method using Flask sessions
- **Role-based access control**: Admin and broker user roles with different permission levels
- **Decorator-based route protection**: Custom decorators for login and admin requirements
- **JWT support**: Additional JWT token support for API endpoints

## Database Architecture
- **SQLAlchemy ORM**: Database abstraction layer with model relationships
- **User management**: Users table with role-based permissions and lead assignment capabilities
- **Lead tracking**: Comprehensive lead lifecycle management with status tracking
- **Configuration storage**: System settings for Meta API integration and lead distribution
- **Audit logging**: Integration logs for API synchronization and system events

## Lead Management System
- **Meta API Integration**: Automated lead fetching from Facebook Lead Ads
- **Lead Distribution Engine**: Configurable distribution modes (round-robin and manual)
- **Status Tracking**: Lead lifecycle management (new, in contact, converted, lost)
- **Assignment System**: Broker-lead relationship management with history tracking

## External API Integration
- **Meta Graph API**: Facebook Lead Ads integration for lead capture
- **Configuration Management**: Secure storage of API credentials and settings
- **Error Handling**: Comprehensive error logging and connection testing
- **Webhook Support**: Prepared for real-time lead notifications

## Frontend Architecture
- **Jinja2 Templates**: Server-side rendering with template inheritance
- **Bootstrap Framework**: Responsive UI with dark theme support
- **JavaScript Enhancement**: Progressive enhancement for better user experience
- **Dashboard System**: Role-specific dashboards with real-time metrics

## Background Processing
- **Scheduled Tasks**: Automated Meta API synchronization every 5 minutes
- **Lead Distribution**: Automatic broker assignment upon lead receipt
- **System Monitoring**: Background health checks and error reporting

# External Dependencies

## Core Framework Dependencies
- **Flask**: Web application framework
- **SQLAlchemy**: Database ORM and connection management
- **Werkzeug**: WSGI utilities including proxy fix for deployment
- **APScheduler**: Background task scheduling

## Authentication & Security
- **Flask-JWT-Extended**: JWT token management
- **Werkzeug Security**: Password hashing and verification utilities

## External API Integration
- **Requests**: HTTP client for Meta Graph API communication
- **Meta Graph API**: Facebook Lead Ads integration for lead capture

## Frontend Dependencies
- **Bootstrap**: UI framework with dark theme support
- **Font Awesome**: Icon library for user interface
- **Chart.js**: Data visualization for reports and analytics

## Development & Deployment
- **Python Logging**: Application logging and error tracking
- **Environment Variables**: Configuration management for sensitive data
- **ProxyFix**: WSGI middleware for proper request handling behind proxies

## Database Support
- **Database URL Configuration**: Environment-based database connection
- **Connection Pooling**: SQLAlchemy engine options for production reliability
- **Migration Support**: Database schema management capabilities