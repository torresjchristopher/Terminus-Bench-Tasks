#ifndef COMMON_H
#define COMMON_H

#include <string>
#include <vector>

namespace utils {

class StringProcessor {
public:
    static std::string reverse(const std::string& input);
    static std::vector<std::string> split(const std::string& input, char delimiter);
    static std::string join(const std::vector<std::string>& parts, const std::string& separator);
};

class MathHelper {
public:
    static int fibonacci(int n);
    static bool isPrime(int n);
    static int gcd(int a, int b);
};

} // namespace utils

#endif // COMMON_H
