cmake_minimum_required(VERSION 3.22)
project(SccacheDemo CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Add source files
file(GLOB SOURCES "src/*.cpp")

# Create executable
add_executable(demo ${SOURCES})

# Add include directories
target_include_directories(demo PRIVATE src)
