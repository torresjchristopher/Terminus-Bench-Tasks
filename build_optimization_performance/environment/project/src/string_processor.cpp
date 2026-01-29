#include "common.h"
#include <algorithm>
#include <sstream>

namespace utils {

std::string StringProcessor::reverse(const std::string& input) {
    std::string result = input;
    std::reverse(result.begin(), result.end());
    return result;
}

std::vector<std::string> StringProcessor::split(const std::string& input, char delimiter) {
    std::vector<std::string> tokens;
    std::stringstream ss(input);
    std::string token;

    while (std::getline(ss, token, delimiter)) {
        tokens.push_back(token);
    }

    return tokens;
}

std::string StringProcessor::join(const std::vector<std::string>& parts, const std::string& separator) {
    if (parts.empty()) return "";

    std::string result = parts[0];
    for (size_t i = 1; i < parts.size(); ++i) {
        result += separator + parts[i];
    }

    return result;
}

} // namespace utils
